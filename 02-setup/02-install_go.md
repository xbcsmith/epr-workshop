# Install Go

The Go programming language is used in the Event-Driven CI/CD workshop. To
install it, follow the steps on the Go website:
[https://go.dev/doc/install](https://go.dev/doc/install).

## Windows

Another way is to download and install the
[Go Windows Installer](https://go.dev/dl/).

## Mac OS

Another way is to install from [homebrew](https://brew.sh/).

```bash
brew install go
```

---

## Linux

Easiest way is to install from the [Go downloads page](https://go.dev/dl/).

```bash
export GOVERSION=1.25.1
export GOARCH=amd64
export GOOS=linux
export GO_CHECKSUM=7716a0d940a0f6ae8e1f3b3f4f36299dc53e31b16840dbd171254312c41ca12e
curl -kLO https://dl.google.com/go/go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
echo "${GO_CHECKSUM} go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz" | sha256sum --check
sudo rm -rfv /usr/local/go
sudo tar -C /usr/local/ -xvzf go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
export PATH=/usr/local/go/bin:$PATH
go version
rm -v go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
```

---

## Tools

Once you have installed go you can install the tools that are used in the
workshop.

---

### golangci-lint

Install golangci-lint by following the instructions on the website:
[https://golangci-lint.run/usage/install/](https://golangci-lint.run/usage/install/)

### alternative install methods for golangci-lint

To install golangci-lint, on a Mac M1, run the following command:

```bash
brew install golangci/tap/golangci-lint
brew upgrade golangci/tap/golangci-lint
```

---

To install golangci-lint on Linux, run the following command:

```bash
export GOLANGCI_LINT_VERSION="2.5.0"
curl -sSfL https://github.com/golangci/golangci-lint/releases/download/v${GOLANGCI_LINT_VERSION}/golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz -o golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz
curl -sSfL https://github.com/golangci/golangci-lint/releases/download/v${GOLANGCI_LINT_VERSION}/golangci-lint-${GOLANGCI_LINT_VERSION}-checksums.txt | grep linux-amd64.tar.gz | sha256sum --check
tar -C $(go env GOPATH)/bin -xvzf golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64/golangci-lint --strip-components 1
rm -vf golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz
```

To run golangci-lint with a Docker container, run the following command:

```bash
docker run --rm -v $(pwd):/app;rw,z -w /app golangci/golangci-lint:v1.56.2 golangci-lint run -v
```

---
