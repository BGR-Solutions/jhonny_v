package durable

import (
	"os"
	"strings"
	"testing"

	"github.com/grafana/alloy/internal/component/loki/process/stages"
	"github.com/grafana/alloy/syntax"
)

func deployedArguments(t *testing.T) Arguments {
	t.Helper()
	data, err := os.ReadFile("/src/durable-config.alloy")
	if err != nil {
		t.Fatal(err)
	}
	text := string(data)
	start, end := strings.Index(text, "\tstage.replace"), strings.LastIndex(text, "\n}")
	var args Arguments
	args.SetToDefault()
	args.Host, args.Endpoint = "http://docker", "http://loki"
	var policy struct {
		Stages []stages.StageConfig `alloy:"stage,enum,optional"`
	}
	if err := syntax.Unmarshal([]byte(text[start:end]), &policy); err != nil {
		t.Fatal(err)
	}
	args.Stages = policy.Stages
	return args
}

func TestDurablePolicyFailsClosed(t *testing.T) {
	deployed := deployedArguments(t)
	if err := deployed.Validate(); err != nil {
		t.Fatal(err)
	}
	tests := map[string]func(*Arguments){
		"wrong-mask": func(args *Arguments) {
			args.Stages[0].ReplaceConfig.Expression = "never-matches"
		},
		"buffering-stage": func(args *Arguments) {
			args.Stages = append(args.Stages, stages.StageConfig{MultilineConfig: &stages.MultilineConfig{}})
		},
		"dropping-stage": func(args *Arguments) {
			args.Stages[4].JSONConfig.DropMalformed = true
		},
		"unsafe-source": func(args *Arguments) {
			args.Stages[0].ReplaceConfig.Source = "extracted"
		},
		"unbounded-readers": func(args *Arguments) {
			args.MaxReaders = 1000000
		},
		"zero-capacity": func(args *Arguments) {
			args.QueueMaxBytes = "0"
		},
	}
	for name, mutate := range tests {
		t.Run(name, func(t *testing.T) {
			args := deployedArguments(t)
			mutate(&args)
			if err := args.Validate(); err == nil {
				t.Fatal("unsafe policy accepted")
			}
		})
	}
}
