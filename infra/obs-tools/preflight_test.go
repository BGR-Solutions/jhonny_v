package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/crypto/bcrypt"
)

func TestCredentialBoundaries(t *testing.T) {
	for _, scenario := range []string{"empty", "duplicate", "wrong-user", "bad-hash", "newline", "too-short", "too-long", "unicode", "directory", "symlink", "public-directory"} {
		t.Run(scenario, func(t *testing.T) {
			dir := t.TempDir()
			if err := os.Chmod(dir, 0700); err != nil {
				t.Fatal(err)
			}
			password := strings.Repeat("q", 32)
			hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.MinCost)
			if err != nil {
				t.Fatal(err)
			}
			for name, content := range map[string]string{"read.htpasswd": "reader:" + string(hash) + "\n", "write.htpasswd": "writer:" + string(hash) + "\n", "write-password": password} {
				if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0600); err != nil {
					t.Fatal(err)
				}
			}
			bad := ""
			target := "write-password"
			switch scenario {
			case "duplicate":
				target = "write.htpasswd"
				bad = "writer:" + string(hash) + "\nwriter:" + string(hash)
			case "wrong-user":
				target = "read.htpasswd"
				bad = "someone:" + string(hash)
			case "bad-hash":
				target = "read.htpasswd"
				bad = "reader:not-bcrypt"
			case "newline":
				bad = password + "\n"
			case "too-short":
				bad = strings.Repeat("q", 31)
			case "too-long":
				bad = strings.Repeat("q", 73)
			case "unicode":
				bad = strings.Repeat("q", 32) + "\xc3\xa9"
			case "directory":
				if err := os.Remove(filepath.Join(dir, target)); err != nil {
					t.Fatal(err)
				}
				if err := os.Mkdir(filepath.Join(dir, target), 0700); err != nil {
					t.Fatal(err)
				}
			case "symlink":
				if err := os.Remove(filepath.Join(dir, target)); err != nil {
					t.Fatal(err)
				}
				if err := os.Symlink("read.htpasswd", filepath.Join(dir, target)); err != nil {
					t.Fatal(err)
				}
			case "public-directory":
				if err := os.Chmod(dir, 0755); err != nil {
					t.Fatal(err)
				}
			}
			if scenario != "directory" && scenario != "symlink" && scenario != "public-directory" {
				if err := os.WriteFile(filepath.Join(dir, target), []byte(bad), 0600); err != nil {
					t.Fatal(err)
				}
			}
			if secrets(dir, "reader", "writer") == nil {
				t.Fatal("invalid credential accepted")
			}
		})
	}
}

func TestWritableDirectory(t *testing.T) {
	dir := t.TempDir()
	if err := writableDirectory(dir); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 0 {
		t.Fatal("write check leaked file")
	}
	if writableDirectory(filepath.Join(dir, "missing")) == nil {
		t.Fatal("missing volume accepted")
	}
}
