# Install Miscellaneous Tools

## Tools

### Git

Git is a fast, scalable, distributed revision control system with an unusually
rich command set that provides both high-level operations and full access to
internals.

[Git Downloads](https://git-scm.com/downloads)

Linux

```bash
dnf install git
```

Mac OS

Apple ships a binary package of Git with Xcode.

or

```bash
brew install git
```

---

### ULID

Universally Unique Lexicographically Sortable Identifier

ULIDs are constructed from two things: a timestamp with millisecond precision,
and some random data.

Timestamps are modeled as uint64 values representing a Unix time in
milliseconds. They can be produced by passing a time.Time to ulid.Timestamp, or
by calling time.Time.UnixMilli and converting the returned value to uint64.

You can download the binaries from the
[ULID releases page](https://github.com/oklog/ulid/releases).

Or you can install ULID with the following command:

```bash
go get github.com/oklog/ulid/v2
```

---

### jq

jq is written in C and has no runtime dependencies, so it should be possible to
build it for nearly any platform. Prebuilt binaries are available for Linux,
macOS and Windows.

The binaries should just run, but on macOS and Linux you may need to make them
executable first using chmod +x jq.

You can download the binaries from the
[jq downloads page](https://jqlang.github.io/jq/download/).

Or you can install jq with the following command:

```bash
brew install jq
```

```bash
sudo dnf install jq
```

---

### VSCode

VSCode is the default editor in the workshop. While not necessary for the
workshop, all demos will be presented using VSCode.

You can download the VSCode installer from the
[VSCode downloads page](https://code.visualstudio.com/download).
