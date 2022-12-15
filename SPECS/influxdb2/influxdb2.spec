%define project github.com/influxdata/influxdb/v2

Name:           influxdb2
Summary:        Scalable datastore for metrics, events, and real-time analytics
License:        MIT
Group:          Productivity/Databases/Servers
Vendor:         Microsoft Corporation
Distribution:   Mariner
Version:        2.4.0
Release:        1%{?dist}
URL:            https://github.com/influxdata/influxdb
Source0:        %{url}%archive/refs/tags/v%{version}#/%{name}-%{version}.tar.gz
# Below is a manually created tarball, no download link.
# We're using pre-populated Go modules from this tarball, since network is disabled during build time.
# How to re-build this file:
#   1. wget https://github.com/influxdata/influxdb/archive/refs/tags/v%%{version}.tar.gz -O %%{name}-%%{version}.tar.gz
#   2. tar -xf %%{name}-%%{version}.tar.gz
#   3. cd %%{name}-%%{version}
#   4. go mod vendor
#   5. tar  --sort=name \
#           --mtime="2021-04-26 00:00Z" \
#           --owner=0 --group=0 --numeric-owner \
#           --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
#           -cf %%{name}-%%{version}-vendor.tar.gz vendor
#
Source1:        %{name}-%{version}-vendor.tar.gz
# Below is a manually created tarball, no download link.
# predownloaded assets include ui assets and swager json. Used to replace fetch-assets and fetch-swagger script.
# How to rebuild this file:
#   1. wget https://github.com/influxdata/influxdb/archive/refs/tags/v%%{version}.tar.gz -O %%{name}-%%{version}.tar.gz
#   2. tar -xf %%{name}-%%{version}.tar.gz
#   3. cd %%{name}-%%{version}
#   4. make generate-web-assets
#   5. cd static
#   6. tar -cvf %%{name}-%%{version}-static-data.tar.gz data/
Source2:        %{name}-%{version}-static-data.tar.gz
BuildRequires:  fdupes
BuildRequires:  go >= 1.18
BuildRequires:  golang-packaging >= 15.0.8
BuildRequires:  pkg-config >= 0.171.0
BuildRequires:  protobuf-devel
BuildRequires:  kernel-headers
BuildRequires:  make
BuildRequires:  rust >= 1.60.0
BuildRequires:  clang
BuildRequires:  tzdata

%description
InfluxDB is an distributed time series database with no external dependencies.
It's useful for recording metrics, events, and performing analytics.

%package        devel
Summary:        InfluxDB development files
Group:          Development/Languages/Golang
Requires:       go
Conflicts:      influxdb 

%description devel
Go sources and other development files for InfluxDB

%prep
%autosetup
# Remove fetching of UI assets and swagger json file, since we provide it ourselves
sed -i 's|static/data/build static/data/swagger.json| |' GNUmakefile

# Remove @v1.2.7.1 because that makes "go install -mod vendor" conflict and not look for vendored package, but download instead.
sed -i 's|protoc-gen-go@v1.27.1|protoc-gen-go|' GNUmakefile

# Add vendor mode to both build and test
sed -i 's/^GO_TEST_ARGS :=/& -mod vendor/' GNUmakefile
sed -i 's/^GO_BUILD_ARGS :=/& -mod vendor/' GNUmakefile

# pkg-config script need to build using vendored package
sed -i 's/^go build/& -mod vendor /' scripts/pkg-config.sh


%build
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH=$PATH:$GOPATH:$GOBIN
tar -xf %{SOURCE1} --no-same-owner

mkdir -pv static
tar -xf %{SOURCE2} -C static/ --no-same-owner

# Build influxdb
mkdir -pv $HOME/go/src/%{project}
rm -rf $HOME/go/src/%{project}/*
cp -avr * $HOME/go/src/%{project}
cd $HOME/go/src/%{project}

export LDFLAGS="-X main.version=%{version}"
make pkg-config
make


%install
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH=$PATH:$GOBIN
cd $HOME/go/src/%{project}

mkdir -p %{buildroot}%{_localstatedir}/log/influxdb
mkdir -p %{buildroot}%{_localstatedir}/lib/influxdb
install -D -m 0755 bin/linux/influxd %{buildroot}/%{_bindir}/influxd

%fdupes %{buildroot}/%{_prefix}

%check
go test ./...

%files
%license LICENSE
%dir %{_sysconfdir}/influxdb2
%{_bindir}/influxd
%{_bindir}/telemetryd
%{_datadir}/influxdb2
%dir %{_tmpfilesdir}
%attr(0755, influxdb, influxdb) %dir %{_localstatedir}/log/influxdb
%attr(0755, influxdb, influxdb) %dir %{_localstatedir}/lib/influxdb

%files devel
%license LICENSE
%dir %{go_contribsrcdir}/github.com
%dir %{go_contribsrcdir}/github.com/influxdata
%{go_contribsrcdir}/github.com/influxdata/influxdb

%changelog