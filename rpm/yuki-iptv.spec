Summary:	IPTV player with EPG support (Astroncia IPTV fork)
Name:		yuki-iptv
Version:	1.0
Release:	1
Group:		Multimedia
License:	GPL-3.0-or-later
URL:		https://github.com/yuki-iptv/yuki-iptv
Source0:	%{name}-%{version}.tar.gz
BuildRequires:	hicolor-icon-theme
BuildRequires:	gettext
Requires:	python3
Requires:	mpv
%if 0%{?sle_version} <= 150500 && 0%{?is_opensuse}
%define use_python_version python311
%else
%define use_python_version python3
%endif
%if 0%{?sle_version} <= 150500 && 0%{?is_opensuse}
%if %{__isa_bits} == 64
Requires:	libmpv.so.1()(64bit)
%else
Requires:	libmpv.so.1
%endif
%else
%if %{__isa_bits} == 64
Requires:	libmpv.so.2()(64bit)
%else
Requires:	libmpv.so.2
%endif
%endif
%if %{defined fedora}
Requires:	%{use_python_version}-qt5
Requires:	%{use_python_version}-pillow
%else
Requires:	%{use_python_version}-qt6
%if %{defined mageia}
Requires:	%{use_python_version}-pillow
%else
%if 0%{?sle_version} <= 150500 && 0%{?is_opensuse}
Requires:	%{use_python_version}-Pillow
%else
Requires:	%{use_python_version}-Wand
%endif
%endif
%endif
Requires:	%{use_python_version}-gobject
Requires:	%{use_python_version}-pydbus
%if 0%{?suse_version} || 0%{?sle_version}
Requires:	%{use_python_version}-Unidecode
%else
Requires:	%{use_python_version}-unidecode
%endif
Requires:	%{use_python_version}-chardet
Requires:	%{use_python_version}-requests
Requires:	%{use_python_version}-setproctitle
Requires:	ffmpeg
Requires:	yt-dlp

%description
IPTV player with EPG support (Astroncia IPTV fork)

%files
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/%{name}
/usr/share/locale/*/*/yuki-iptv.mo
%{_prefix}/lib/%{name}
/usr/share/icons/hicolor/scalable/apps/yuki-iptv.svg
/usr/share/metainfo/yuki-iptv.appdata.xml

%dir /usr/share/locale/*
%dir /usr/share/locale/*/*

%global debug_package %{nil}

%post
ldconfig

%prep
%setup -q

%build
make
sed -i "s/__DEB_VERSION__/%{version}/g" usr/lib/yuki-iptv/yuki-iptv.py

%install
cp -af usr %{buildroot}
