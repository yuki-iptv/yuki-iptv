Summary:	IPTV player with EPG support (Astroncia IPTV fork)
Name:		yuki-iptv
Version:	1.0
Release:	1
Group:		Multimedia
License:	GPL-3.0-or-later
URL:		https://github.com/yuki-iptv/yuki-iptv
Source0:	%{name}-%{version}.tar.gz
Requires:	python3
Requires:	mpv
%if %{__isa_bits} == 64
Requires:	libmpv.so.2()(64bit)
%else
Requires:	libmpv.so.2
%endif
%if %{defined fedora}
Requires:	python3-qt5
Requires:	python3-pillow
%else
Requires:	python3-qt6
Requires:	python3-Wand
%endif
Requires:	python3-gobject
Requires:	python3-pydbus
%if 0%{?suse_version} || 0%{?sle_version}
Requires:	python3-Unidecode
%else
Requires:	python3-unidecode
%endif
Requires:	python3-chardet
Requires:	python3-requests
Requires:	python3-setproctitle
Requires:	ffmpeg
Requires:	yt-dlp

%description
IPTV player with EPG support (Astroncia IPTV fork)

%files
/usr/*

%global debug_package %{nil}

%post
ldconfig

%prep
%setup -q

%build
#nothing

%install
cp -af usr %{buildroot}
