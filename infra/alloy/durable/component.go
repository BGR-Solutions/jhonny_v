package durable

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/grafana/alloy/internal/component"
	"github.com/grafana/alloy/internal/component/common/loki"
	"github.com/grafana/alloy/internal/component/discovery"
	"github.com/grafana/alloy/internal/component/loki/process/stages"
	"github.com/grafana/alloy/internal/featuregate"
	"github.com/grafana/alloy/syntax/alloytypes"
	"github.com/grafana/loki/pkg/push"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/common/model"
)

func init() {
	component.Register(component.Registration{
		Name: "loki.source.docker_durable", Stability: featuregate.StabilityGenerallyAvailable,
		Args: Arguments{},
		Build: func(options component.Options, args component.Arguments) (component.Component, error) {
			return New(options, args.(Arguments))
		},
	})
}

// Arguments configures the native source. Only targets may change without restart.
type Arguments struct {
	Host          string               `alloy:"host,attr"`
	Targets       []discovery.Target   `alloy:"targets,attr"`
	Endpoint      string               `alloy:"endpoint,attr"`
	Username      string               `alloy:"username,attr"`
	Password      alloytypes.Secret    `alloy:"password,attr"`
	QueueMaxBytes string               `alloy:"queue_max_bytes,attr,optional"`
	MaxReaders    int                  `alloy:"max_readers,attr,optional"`
	Stages        []stages.StageConfig `alloy:"stage,enum"`
}

var maskExpressions = [...]string{
	`(?i)bearer\s+([A-Za-z0-9._~+/=-]+)`,
	`\b(sk-[A-Za-z0-9_-]{16,})`,
	`(?i)(?:password|passwd|pwd|secret|token|api_key|apikey)"?\s*[:=]\s*"((?:[^"\\]|\\.)*)"`,
	`(?i)(?:password|passwd|pwd|secret|token|api_key|apikey)"?\s*[:=]\s*([^"\s,&}]+)`,
}

// SetToDefault implements syntax.Defaulter.
func (a *Arguments) SetToDefault() {
	a.QueueMaxBytes, a.MaxReaders = "268435456", 128
}

// Validate rejects asynchronous, buffering, dropping or payload-logging stages.
func (a *Arguments) Validate() error {
	limit, err := strconv.ParseUint(a.QueueMaxBytes, 10, 63)
	if err != nil || limit == 0 || a.MaxReaders < 1 || a.MaxReaders > 1024 {
		return errors.New("queue_max_bytes must be positive; max_readers must be 1..1024")
	}
	for _, address := range []string{a.Host, a.Endpoint} {
		parsed, err := url.Parse(address)
		if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") || parsed.Host == "" ||
			parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" {
			return errors.New("endpoints must be HTTP(S) without embedded credentials or query")
		}
	}
	// Only these stateless synchronous stages have an audited commit boundary.
	replace, jsonStage, metadata := 0, 0, 0
	for _, stage := range a.Stages {
		if stage.ReplaceConfig != nil {
			copy := stage
			copy.ReplaceConfig = nil
			if !reflect.DeepEqual(copy, stages.StageConfig{}) || stage.ReplaceConfig.Source != "" ||
				stage.ReplaceConfig.Replace != "<redacted>" || replace >= len(maskExpressions) ||
				stage.ReplaceConfig.Expression != maskExpressions[replace] || jsonStage != 0 {
				return errors.New("only full-line masking stages are supported")
			}
			replace++
		} else if stage.JSONConfig != nil {
			copy := stage
			copy.JSONConfig = nil
			if !reflect.DeepEqual(copy, stages.StageConfig{}) || stage.JSONConfig.DropMalformed ||
				stage.JSONConfig.Source != nil || replace < 4 || jsonStage != 0 ||
				stage.JSONConfig.Regex != "" || !reflect.DeepEqual(stage.JSONConfig.Expressions,
				map[string]string{"level": "", "trace_id": "", "span_id": ""}) {
				return errors.New("JSON extraction must follow masking and cannot drop records")
			}
			jsonStage++
		} else if stage.StructuredMetadata != nil {
			copy := stage
			copy.StructuredMetadata = nil
			if !reflect.DeepEqual(copy, stages.StageConfig{}) || jsonStage != 1 || metadata != 0 {
				return errors.New("metadata must follow masked JSON extraction")
			}
			if stage.StructuredMetadata.Regex != "" || len(stage.StructuredMetadata.Values) != 3 {
				return errors.New("only level, trace_id and span_id metadata are supported")
			}
			for _, name := range []string{"level", "trace_id", "span_id"} {
				value, ok := stage.StructuredMetadata.Values[name]
				if !ok || (value != nil && *value != "") {
					return errors.New("metadata must use the masked extracted field")
				}
			}
			metadata++
		} else {
			return errors.New("unsupported stage in durable source")
		}
	}
	if replace != 4 || jsonStage != 1 || metadata != 1 || len(a.Stages) != 6 {
		return errors.New("durable source requires four masks, JSON extraction and metadata")
	}
	return nil
}

type sourceReader struct {
	cancel context.CancelFunc
	done   chan struct{}
	name   string
}

// Component owns source readers, synchronous masking, storage and acknowledged delivery.
type Component struct {
	opts         component.Options
	mut          sync.Mutex
	args         Arguments
	changed      chan struct{}
	queue        *diskQueue
	receipts     *prometheus.CounterVec
	errors       prometheus.Counter
	deliveryBad  atomic.Bool
	sourceErrors atomic.Int64
	capacityBad  atomic.Bool
}

// New opens durable state fail-closed before any Docker payload is read.
func New(options component.Options, args Arguments) (*Component, error) {
	if err := args.Validate(); err != nil {
		return nil, err
	}
	limit, _ := strconv.ParseUint(args.QueueMaxBytes, 10, 63)
	queue, err := openQueue(filepath.Join(options.DataPath, "queue.db"), limit)
	if err != nil {
		return nil, err
	}
	c := &Component{opts: options, args: args, queue: queue, changed: make(chan struct{}, 1)}
	c.receipts = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "loki_source_docker_durable_receipts_total", Help: "Masked records synchronously committed; active sources only.",
	}, []string{"container", "stream"})
	c.errors = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "loki_source_docker_durable_delivery_errors_total", Help: "Delivery attempts without a durable Loki acknowledgement.",
	})
	options.Registerer.MustRegister(c.receipts, c.errors,
		prometheus.NewGaugeFunc(prometheus.GaugeOpts{
			Name: "loki_source_docker_durable_pending_records", Help: "Records retained until Loki returns 204.",
		}, func() float64 { count, _ := queue.stats(); return float64(count) }),
		prometheus.NewGaugeFunc(prometheus.GaugeOpts{
			Name: "loki_source_docker_durable_pending_bytes", Help: "Logical serialized payload bytes, excluding database overhead.",
		}, func() float64 { _, size := queue.stats(); return float64(size) }),
		prometheus.NewGaugeFunc(prometheus.GaugeOpts{
			Name: "loki_source_docker_durable_paused_sources", Help: "Source calls blocked by the disk queue logical limit.",
		}, func() float64 { return float64(queue.paused.Load()) }),
	)
	return c, nil
}

// Update accepts discovery changes; immutable delivery/storage/policy needs restart.
func (c *Component) Update(value component.Arguments) error {
	args := value.(Arguments)
	c.mut.Lock()
	defer c.mut.Unlock()
	old, next := c.args, args
	old.Targets, next.Targets = nil, nil
	if !reflect.DeepEqual(old, next) {
		return errors.New("durable source policy changes require restarting Alloy")
	}
	c.args = args
	select {
	case c.changed <- struct{}{}:
	default:
	}
	return nil
}

// CurrentHealth exposes degradation without payloads, addresses or credentials.
func (c *Component) CurrentHealth() component.Health {
	if c.queue.failed.Load() || c.queue.paused.Load() > 0 || c.deliveryBad.Load() ||
		c.sourceErrors.Load() > 0 || c.capacityBad.Load() {
		return component.Health{Health: component.HealthTypeUnhealthy,
			Message: "durable source degraded: delivery, storage, capacity or Docker read unavailable"}
	}
	return component.Health{Health: component.HealthTypeHealthy, Message: "durable source accepting and delivering"}
}

// Run replays stored records independently of Docker producer availability.
func (c *Component) Run(ctx context.Context) error {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	var workers sync.WaitGroup
	workers.Add(1)
	go func() { defer workers.Done(); c.deliver(ctx) }()
	readers := make(map[string]*sourceReader)
	defer func() {
		cancel()
		for _, reader := range readers {
			reader.cancel()
		}
		for _, reader := range readers {
			<-reader.done
		}
		workers.Wait()
		c.queue.close()
	}()
	c.opts.Logger.Info("durable Docker source started", "queue_limit_bytes", c.queue.limit)
	for {
		c.mut.Lock()
		args := c.args
		c.mut.Unlock()
		targets := make(map[string]model.LabelSet)
		for _, target := range args.Targets {
			labels := target.LabelSet()
			id := string(labels["__meta_docker_container_id"])
			if id != "" && len(id) <= 128 {
				targets[id] = labels
			}
		}
		for id, reader := range readers {
			if _, found := targets[id]; !found {
				reader.cancel()
				<-reader.done
				c.receipts.DeleteLabelValues(reader.name, "stdout")
				c.receipts.DeleteLabelValues(reader.name, "stderr")
				delete(readers, id)
			}
		}
		c.capacityBad.Store(len(targets) > args.MaxReaders)
		ids := make([]string, 0, len(targets))
		for id := range targets {
			ids = append(ids, id)
		}
		sort.Strings(ids)
		for _, id := range ids {
			if readers[id] != nil || len(readers) >= args.MaxReaders {
				continue
			}
			readerCtx, stop := context.WithCancel(ctx)
			reader := &sourceReader{cancel: stop, done: make(chan struct{}),
				name: strings.TrimPrefix(string(targets[id]["__meta_docker_container_name"]), "/")}
			readers[id] = reader
			go func(id string, target model.LabelSet) {
				defer close(reader.done)
				c.readContainer(readerCtx, args, id, target)
			}(id, targets[id])
		}
		select {
		case <-ctx.Done():
			return nil
		case <-c.changed:
		}
	}
}

func (c *Component) deliver(ctx context.Context) {
	c.mut.Lock()
	args := c.args
	c.mut.Unlock()
	client := &http.Client{Transport: boundedTransport(), Timeout: 10 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	defer client.CloseIdleConnections()
	delay := 100 * time.Millisecond
	for ctx.Err() == nil {
		err := sendOldest(ctx, c.queue, client, args.Endpoint, args.Username, string(args.Password))
		if err == nil {
			c.deliveryBad.Store(false)
			delay = 100 * time.Millisecond
			continue
		}
		if !errors.Is(err, errEmpty) {
			c.deliveryBad.Store(true)
			c.errors.Inc()
			if delay < 5*time.Second {
				delay *= 2
				if delay > 5*time.Second {
					delay = 5 * time.Second
				}
			}
		}
		timer := time.NewTimer(delay)
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
	}
}

func (c *Component) readContainer(ctx context.Context, args Arguments, id string, target model.LabelSet) {
	client := &http.Client{Transport: boundedTransport(), CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	defer client.CloseIdleConnections()
	consumer := &queueConsumer{queue: c.queue, source: id, receipt: func(labels model.LabelSet) {
		c.receipts.WithLabelValues(string(labels["container"]), string(labels["stream"])).Inc()
	}}
	// Stage diagnostics can contain raw lines even at debug level; never expose them.
	pipeline, err := stages.NewPipelineConsumer(slog.New(slog.NewJSONHandler(io.Discard, nil)),
		prometheus.NewRegistry(), c.opts.MinStability, args.Stages, consumer)
	if err != nil {
		c.sourceErrors.Add(1)
		defer c.sourceErrors.Add(-1)
		<-ctx.Done()
		return
	}

	defer pipeline.Stop()
	bad := false
	defer func() {
		if bad {
			c.sourceErrors.Add(-1)
		}
	}()
	for ctx.Err() == nil {
		err := c.readConnection(ctx, client, args.Host, id, target, pipeline, func() {
			if bad {
				c.sourceErrors.Add(-1)
				bad = false
			}
		})
		if ctx.Err() != nil {
			return
		}
		if err != nil && !bad {
			c.sourceErrors.Add(1)
			bad = true
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(time.Second):
		}
		// Reconnect intentionally rereads ALL retained history. Timestamps are not
		// monotonic, and cannot safely authorize skipping an uncommitted record.
	}
}

func (c *Component) readConnection(ctx context.Context, client *http.Client, host, id string, target model.LabelSet, pipeline *stages.PipelineConsumer, connected func()) error {
	inspectCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	request, _ := http.NewRequestWithContext(inspectCtx, http.MethodGet, host+"/containers/"+id+"/json", nil)
	response, err := client.Do(request)
	if err != nil {
		cancel()
		return errors.New("Docker inspection unavailable")
	}
	var info struct {
		Config struct{ Tty bool }
	}
	err = json.NewDecoder(io.LimitReader(response.Body, 1024*1024)).Decode(&info)
	response.Body.Close()
	cancel()
	if err != nil || response.StatusCode != 200 {
		return errors.New("Docker inspection failed")
	}
	request, _ = http.NewRequestWithContext(ctx, http.MethodGet,
		host+"/containers/"+id+"/logs?stdout=1&stderr=1&timestamps=1&follow=1&tail=all", nil)
	response, err = client.Do(request)
	if err != nil {
		return errors.New("Docker logs unavailable")
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		return errors.New("Docker logs request failed")
	}
	connected()
	return readDocker(response.Body, info.Config.Tty, func(record rawRecord) error {
		labels := model.LabelSet{
			"container": model.LabelValue(strings.TrimPrefix(string(target["__meta_docker_container_name"]), "/")),
			"stream":    model.LabelValue(record.Stream),
		}
		for label, source := range map[string]string{
			"compose_project": "__meta_docker_container_label_com_docker_compose_project",
			"compose_service": "__meta_docker_container_label_com_docker_compose_service",
		} {
			if value := target[model.LabelName(source)]; value != "" {
				labels[model.LabelName(label)] = value
			}
		}
		batch := loki.NewBatch()
		batch.AddEntry(labels, 0, push.Entry{Timestamp: record.Time, Line: record.Line})
		return pipeline.Consume(ctx, batch)
	})
}
