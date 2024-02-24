# Install Go

The Golang programming language is used in the Event-Driven CI/CD workshop. To install it, follow the steps on the Golang website: [https://go.dev/doc/install](https://go.dev/doc/install).

## Windows

Another way is to download and install the [Golang Windows Installer](https://go.dev/dl/).

## Mac M1

Another way is to install from [homebrew](https://brew.sh/).

```bash
brew install go
```

## Linux

Easiest way is to install from the [Go downloads page](https://go.dev/dl/).

```bash
export GOVERSION=1.22.0
export GOARCH=amd64
export GOOS=linux
export GO_CHECKSUM=f6c8a87aa03b92c4b0bf3d558e28ea03006eb29db78917daec5cfb6ec1046265
curl -kLO https://dl.google.com/go/go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
echo "${GO_CHECKSUM} go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz" | sha256sum --check
sudo rm -rfv /usr/local/go
sudo tar -C /usr/local/ -xvzf go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
export PATH=/usr/local/go/bin:$PATH
go version
rm -v go${GOVERSION}.${GOOS}-${GOARCH}.tar.gz
```

## Tools

Once you have installed go you can install the tools that are used in the workshop.

### golangci-lint

Install golangci-lint by following the instructions on the website: [https://golangci-lint.run/usage/install/](https://golangci-lint.run/usage/install/)


### go tools

Install the tools with the following commands:

```bash
go install golang.org/x/tools/...@latest
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
go install github.com/uudashr/gocognit/cmd/gocognit@latest
go install github.com/go-critic/go-critic/cmd/gocritic@latest
go install github.com/wadey/gocovmerge@latest
go install github.com/axw/gocov/gocov@latest
go install github.com/AlekSi/gocov-xml@latest
go install github.com/tebeka/go2xunit@latest
go install github.com/josephspurrier/goversioninfo/cmd/goversioninfo@latest
go install github.com/golang/protobuf/protoc-gen-go@latest
```

### alternative install methods for golangci-lint

To install golangci-lint, on a Mac M1, run the following command:

```bash
brew install golangci/tap/golangci-lint
brew upgrade golangci/tap/golangci-lint
```

To install golangci-lint on Linux, run the following command:

```bash
export GOLANGCI_LINT_VERSION="1.56.2"
curl -sSfL https://github.com/golangci/golangci-lint/releases/download/v${GOLANGCI_LINT_VERSION}/golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz -o golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz
curl -sSfL https://github.com/golangci/golangci-lint/releases/download/v${GOLANGCI_LINT_VERSION}/golangci-lint-${GOLANGCI_LINT_VERSION}-checksums.txt | grep linux-amd64.tar.gz | sha256sum --check
tar -C $(go env GOPATH)/bin -xvzf golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64/golangci-lint --strip-components 1
rm -vf golangci-lint-${GOLANGCI_LINT_VERSION}-linux-amd64.tar.gz
```

To run golangci-lint with a Docker container, run the following command:

```bash
docker run --rm -v $(pwd):/app;rw,z -w /app golangci/golangci-lint:v1.56.2 golangci-lint run -v
```