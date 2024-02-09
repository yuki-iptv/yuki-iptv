#
# Copyright (c) 2024 Ame-chan-angel <amechanangel@proton.me>
#
# This file is part of yuki-iptv.
#
# yuki-iptv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# yuki-iptv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License.
# Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
# License - https://creativecommons.org/licenses/by/4.0/
#
import logging
import gi.repository.Gio
import gi.repository.GLib

logger = logging.getLogger(__name__)

mpris_xml = """
<?xml version="1.0" ?>
<node name="/Player_Interface" xmlns:tp="http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0">
  <interface name="org.mpris.MediaPlayer2.Player">

    <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
      <p>
        This interface implements the methods for querying and providing basic
        control over what is currently playing.
      </p>
    </tp:docstring>

    <tp:enum name="Playback_Status" tp:name-for-bindings="Playback_Status" type="s">
      <tp:enumvalue suffix="Playing" value="Playing">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>A track is currently playing.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="Paused" value="Paused">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>A track is currently paused.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="Stopped" value="Stopped">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>There is no track currently playing.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A playback state.</p>
      </tp:docstring>
    </tp:enum>

    <tp:enum name="Loop_Status" tp:name-for-bindings="Loop_Status" type="s">
      <tp:enumvalue suffix="None" value="None">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The playback will stop when there are no more tracks to play</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="Track" value="Track">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The current track will start again from the begining once it has finished playing</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="Playlist" value="Playlist">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The playback loops through a list of tracks</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A repeat / loop status</p>
      </tp:docstring>
    </tp:enum>

    <tp:simple-type name="Track_Id" type="o" array-name="Track_Id_List">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Unique track identifier.</p>
        <p>
          If the media player implements the TrackList interface and allows
          the same track to appear multiple times in the tracklist,
          this must be unique within the scope of the tracklist.
        </p>
        <p>
          Note that this should be a valid D-Bus object id, although clients
          should not assume that any object is actually exported with any
          interfaces at that path.
        </p>
        <p>
          Media players may not use any paths starting with
          <literal>/org/mpris</literal> unless explicitly allowed by this specification.
          Such paths are intended to have special meaning, such as
          <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
          to indicate "no track".
        </p>
        <tp:rationale>
          <p>
            This is a D-Bus object id as that is the definitive way to have
            unique identifiers on D-Bus.  It also allows for future optional
            expansions to the specification where tracks are exported to D-Bus
            with an interface similar to org.gnome.UPnP.MediaItem2.
          </p>
        </tp:rationale>
      </tp:docstring>
    </tp:simple-type>

    <tp:simple-type name="Playback_Rate" type="d">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A playback rate</p>
        <p>
          This is a multiplier, so a value of 0.5 indicates that playback is
          happening at half speed, while 1.5 means that 1.5 seconds of "track time"
          is consumed every second.
        </p>
      </tp:docstring>
    </tp:simple-type>

    <tp:simple-type name="Volume" type="d">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Audio volume level</p>
        <ul>
          <li>0.0 means mute.</li>
          <li>1.0 is a sensible maximum volume level (ex: 0dB).</li>
        </ul>
        <p>
          Note that the volume may be higher than 1.0, although generally
          clients should not attempt to set it above 1.0.
        </p>
      </tp:docstring>
    </tp:simple-type>

    <tp:simple-type name="Time_In_Us" type="x">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Time in microseconds.</p>
      </tp:docstring>
    </tp:simple-type>

    <method name="Next" tp:name-for-bindings="Next">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Skips to the next track in the tracklist.</p>
        <p>
          If there is no next track (and endless playback and track
          repeat are both off), stop playback.
        </p>
        <p>If playback is paused or stopped, it remains that way.</p>
        <p>
          If <tp:member-ref>CanGoNext</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect.
        </p>
      </tp:docstring>
    </method>

    <method name="Previous" tp:name-for-bindings="Previous">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Skips to the previous track in the tracklist.</p>
        <p>
          If there is no previous track (and endless playback and track
          repeat are both off), stop playback.
        </p>
        <p>If playback is paused or stopped, it remains that way.</p>
        <p>
          If <tp:member-ref>CanGoPrevious</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect.
        </p>
      </tp:docstring>
    </method>

    <method name="Pause" tp:name-for-bindings="Pause">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Pauses playback.</p>
        <p>If playback is already paused, this has no effect.</p>
        <p>
          Calling Play after this should cause playback to start again
          from the same position.
        </p>
        <p>
          If <tp:member-ref>CanPause</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect.
        </p>
      </tp:docstring>
    </method>

    <method name="PlayPause" tp:name-for-bindings="PlayPause">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Pauses playback.</p>
        <p>If playback is already paused, resumes playback.</p>
        <p>If playback is stopped, starts playback.</p>
        <p>
          If <tp:member-ref>CanPause</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect and raise an error.
        </p>
      </tp:docstring>
    </method>

    <method name="Stop" tp:name-for-bindings="Stop">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Stops playback.</p>
        <p>If playback is already stopped, this has no effect.</p>
        <p>
          Calling Play after this should cause playback to
          start again from the beginning of the track.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect and raise an error.
        </p>
      </tp:docstring>
    </method>

    <method name="Play" tp:name-for-bindings="Play">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Starts or resumes playback.</p>
        <p>If already playing, this has no effect.</p>
        <p>If paused, playback resumes from the current position.</p>
        <p>If there is no track to play, this has no effect.</p>
        <p>
          If <tp:member-ref>CanPlay</tp:member-ref> is
          <strong>false</strong>, attempting to call this method should have
          no effect.
        </p>
      </tp:docstring>
    </method>

    <method name="Seek" tp:name-for-bindings="Seek">
      <arg direction="in" type="x" name="Offset" tp:type="Time_In_Us">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The number of microseconds to seek forward.</p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Seeks forward in the current track by the specified number
          of microseconds.
        </p>
        <p>
          A negative value seeks back. If this would mean seeking
          back further than the start of the track, the position
          is set to 0.
        </p>
        <p>
          If the value passed in would mean seeking beyond the end
          of the track, acts like a call to Next.
        </p>
        <p>
          If the <tp:member-ref>CanSeek</tp:member-ref> property is false,
          this has no effect.
        </p>
      </tp:docstring>
    </method>

    <method name="SetPosition" tp:name-for-bindings="Set_Position">
      <arg direction="in" type="o" tp:type="Track_Id" name="TrackId">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The currently playing track's identifier.</p>
          <p>
            If this does not match the id of the currently-playing track,
            the call is ignored as "stale".
          </p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            is <em>not</em> a valid value for this argument.
          </p>
        </tp:docstring>
      </arg>
      <arg direction="in" type="x" tp:type="Time_In_Us" name="Position">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Track position in microseconds.</p>
          <p>This must be between 0 and &lt;track_length&gt;.</p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Sets the current track position in microseconds.</p>
        <p>If the Position argument is less than 0, do nothing.</p>
        <p>
          If the Position argument is greater than the track length,
          do nothing.
        </p>
        <p>
          If the <tp:member-ref>CanSeek</tp:member-ref> property is false,
          this has no effect.
        </p>
        <tp:rationale>
          <p>
            The reason for having this method, rather than making
            <tp:member-ref>Position</tp:member-ref> writable, is to include
            the TrackId argument to avoid race conditions where a client tries
            to seek to a position when the track has already changed.
          </p>
        </tp:rationale>
      </tp:docstring>
    </method>

    <method name="OpenUri" tp:name-for-bindings="Open_Uri">
      <arg direction="in" type="s" tp:type="Uri" name="Uri">
        <tp:docstring>
          <p>
            Uri of the track to load. Its uri scheme should be an element of the
            <literal>org.mpris.MediaPlayer2.SupportedUriSchemes</literal>
            property and the mime-type should match one of the elements of the
            <literal>org.mpris.MediaPlayer2.SupportedMimeTypes</literal>.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Opens the Uri given as an argument</p>
        <p>If the playback is stopped, starts playing</p>
        <p>
          If the uri scheme or the mime-type of the uri to open is not supported,
          this method does nothing and may raise an error.  In particular, if the
          list of available uri schemes is empty, this method may not be
          implemented.
        </p>
        <p>Clients should not assume that the Uri has been opened as soon as this
           method returns. They should wait until the mpris:trackid field in the
           <tp:member-ref>Metadata</tp:member-ref> property changes.
        </p>
        <p>
          If the media player implements the TrackList interface, then the
          opened track should be made part of the tracklist, the
          <literal>org.mpris.MediaPlayer2.TrackList.TrackAdded</literal> or
          <literal>org.mpris.MediaPlayer2.TrackList.TrackListReplaced</literal>
          signal should be fired, as well as the
          <literal>org.freedesktop.DBus.Properties.PropertiesChanged</literal>
          signal on the tracklist interface.
        </p>
      </tp:docstring>
    </method>

    <property name="PlaybackStatus" tp:name-for-bindings="Playback_Status" type="s" tp:type="Playback_Status" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The current playback status.</p>
        <p>
          May be "Playing", "Paused" or "Stopped".
        </p>
      </tp:docstring>
    </property>

    <property name="LoopStatus" type="s" access="readwrite"
              tp:name-for-bindings="Loop_Status" tp:type="Loop_Status">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <annotation name="org.mpris.MediaPlayer2.property.optional" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The current loop / repeat status</p>
        <p>May be:
          <ul>
            <li>"None" if the playback will stop when there are no more tracks to play</li>
            <li>"Track" if the current track will start again from the begining once it has finished playing</li>
            <li>"Playlist" if the playback loops through a list of tracks</li>
          </ul>
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, attempting to set this property should have
          no effect and raise an error.
        </p>
      </tp:docstring>
    </property>

    <property name="Rate" tp:name-for-bindings="Rate" type="d" tp:type="Playback_Rate" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The current playback rate.</p>
        <p>
          The value must fall in the range described by
          <tp:member-ref>MinimumRate</tp:member-ref> and
          <tp:member-ref>MaximumRate</tp:member-ref>, and must not be 0.0.  If
          playback is paused, the <tp:member-ref>PlaybackStatus</tp:member-ref>
          property should be used to indicate this.  A value of 0.0 should not
          be set by the client.  If it is, the media player should act as
          though <tp:member-ref>Pause</tp:member-ref> was called.
        </p>
        <p>
          If the media player has no ability to play at speeds other than the
          normal playback rate, this must still be implemented, and must
          return 1.0.  The <tp:member-ref>MinimumRate</tp:member-ref> and
          <tp:member-ref>MaximumRate</tp:member-ref> properties must also be
          set to 1.0.
        </p>
        <p>
          Not all values may be accepted by the media player.  It is left to
          media player implementations to decide how to deal with values they
          cannot use; they may either ignore them or pick a "best fit" value.
          Clients are recommended to only use sensible fractions or multiples
          of 1 (eg: 0.5, 0.25, 1.5, 2.0, etc).
        </p>
        <tp:rationale>
          <p>
            This allows clients to display (reasonably) accurate progress bars
            without having to regularly query the media player for the current
            position.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="Shuffle" tp:name-for-bindings="Shuffle" type="b" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <annotation name="org.mpris.MediaPlayer2.property.optional" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          A value of <strong>false</strong> indicates that playback is
          progressing linearly through a playlist, while <strong>true</strong>
          means playback is progressing through a playlist in some other order.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, attempting to set this property should have
          no effect and raise an error.
        </p>
      </tp:docstring>
    </property>

    <property name="Metadata" tp:name-for-bindings="Metadata" type="a{sv}" tp:type="Metadata_Map" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The metadata of the current element.</p>
        <p>
          If there is a current track, this must have a "mpris:trackid" entry
          (of D-Bus type "o") at the very least, which contains a D-Bus path that
          uniquely identifies this track.
        </p>
        <p>
          See the type documentation for more details.
        </p>
      </tp:docstring>
    </property>

    <property name="Volume" type="d" tp:type="Volume" tp:name-for-bindings="Volume" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true" />
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The volume level.</p>
        <p>
          When setting, if a negative value is passed, the volume
          should be set to 0.0.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, attempting to set this property should have
          no effect and raise an error.
        </p>
      </tp:docstring>
    </property>

    <property name="Position" type="x" tp:type="Time_In_Us" tp:name-for-bindings="Position" access="read">
        <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>
            The current track position in microseconds, between 0 and
            the 'mpris:length' metadata entry (see Metadata).
          </p>
          <p>
            Note: If the media player allows it, the current playback position
            can be changed either the SetPosition method or the Seek method on
            this interface.  If this is not the case, the
            <tp:member-ref>CanSeek</tp:member-ref> property is false, and
            setting this property has no effect and can raise an error.
          </p>
          <p>
            If the playback progresses in a way that is inconstistant with the
            <tp:member-ref>Rate</tp:member-ref> property, the
            <tp:member-ref>Seeked</tp:member-ref> signal is emited.
          </p>
        </tp:docstring>
    </property>

    <property name="MinimumRate" tp:name-for-bindings="Minimum_Rate" type="d" tp:type="Playback_Rate" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The minimum value which the <tp:member-ref>Rate</tp:member-ref>
          property can take.
          Clients should not attempt to set the
          <tp:member-ref>Rate</tp:member-ref> property below this value.
        </p>
        <p>
          Note that even if this value is 0.0 or negative, clients should
          not attempt to set the <tp:member-ref>Rate</tp:member-ref> property
          to 0.0.
        </p>
        <p>This value should always be 1.0 or less.</p>
      </tp:docstring>
    </property>

    <property name="MaximumRate" tp:name-for-bindings="Maximum_Rate" type="d" tp:type="Playback_Rate" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The maximum value which the <tp:member-ref>Rate</tp:member-ref>
          property can take.
          Clients should not attempt to set the
          <tp:member-ref>Rate</tp:member-ref> property above this value.
        </p>
        <p>
          This value should always be 1.0 or greater.
        </p>
      </tp:docstring>
    </property>

    <property name="CanGoNext" tp:name-for-bindings="Can_Go_Next" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Whether the client can call the <tp:member-ref>Next</tp:member-ref>
          method on this interface and expect the current track to change.
        </p>
        <p>
          If it is unknown whether a call to <tp:member-ref>Next</tp:member-ref> will
          be successful (for example, when streaming tracks), this property should
          be set to <strong>true</strong>.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, this property should also be
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            Even when playback can generally be controlled, there may not
            always be a next track to move to.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanGoPrevious" tp:name-for-bindings="Can_Go_Previous" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Whether the client can call the
          <tp:member-ref>Previous</tp:member-ref> method on this interface and
          expect the current track to change.
        </p>
        <p>
          If it is unknown whether a call to <tp:member-ref>Previous</tp:member-ref>
          will be successful (for example, when streaming tracks), this property
          should be set to <strong>true</strong>.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, this property should also be
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            Even when playback can generally be controlled, there may not
            always be a next previous to move to.
          </p>
        </tp:rationale>

      </tp:docstring>
    </property>

    <property name="CanPlay" tp:name-for-bindings="Can_Play" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Whether playback can be started using
           <tp:member-ref>Play</tp:member-ref> or
           <tp:member-ref>PlayPause</tp:member-ref>.
        </p>
        <p>
          Note that this is related to whether there is a "current track": the
          value should not depend on whether the track is currently paused or
          playing.  In fact, if a track is currently playing (and
          <tp:member-ref>CanControl</tp:member-ref> is <strong>true</strong>),
          this should be <strong>true</strong>.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, this property should also be
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            Even when playback can generally be controlled, it may not be
            possible to enter a "playing" state, for example if there is no
            "current track".
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanPause" tp:name-for-bindings="Can_Pause" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Whether playback can be paused using
           <tp:member-ref>Pause</tp:member-ref> or
           <tp:member-ref>PlayPause</tp:member-ref>.
        </p>
        <p>
          Note that this is an intrinsic property of the current track: its
          value should not depend on whether the track is currently paused or
          playing.  In fact, if playback is currently paused (and
          <tp:member-ref>CanControl</tp:member-ref> is <strong>true</strong>),
          this should be <strong>true</strong>.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, this property should also be
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            Not all media is pausable: it may not be possible to pause some
            streamed media, for example.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanSeek" tp:name-for-bindings="Can_Seek" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Whether the client can control the playback position using
          <tp:member-ref>Seek</tp:member-ref> and
          <tp:member-ref>SetPosition</tp:member-ref>.  This may be different for
          different tracks.
        </p>
        <p>
          If <tp:member-ref>CanControl</tp:member-ref> is
          <strong>false</strong>, this property should also be
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            Not all media is seekable: it may not be possible to seek when
            playing some streamed media, for example.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanControl" tp:name-for-bindings="Can_Control" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Whether the media player may be controlled over this interface.</p>
        <p>
          This property is not expected to change, as it describes an intrinsic
          capability of the implementation.
        </p>
        <p>
          If this is <strong>false</strong>, clients should assume that all
          properties on this interface are read-only (and will raise errors
          if writing to them is attempted), no methods are implemented
          and all other properties starting with "Can" are also
          <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            This allows clients to determine whether to present and enable
            controls to the user in advance of attempting to call methods
            and write to properties.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <signal name="Seeked" tp:name-for-bindings="Seeked">
      <arg name="Position" type="x" tp:type="Time_In_Us">
        <tp:docstring>
          <p>The new position, in microseconds.</p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Indicates that the track position has changed in a way that is
          inconsistant with the current playing state.
        </p>
        <p>When this signal is not received, clients should assume that:</p>
        <ul>
          <li>
            When playing, the position progresses according to the rate property.
          </li>
          <li>When paused, it remains constant.</li>
        </ul>
        <p>
          This signal does not need to be emitted when playback starts
          or when the track changes, unless the track is starting at an
          unexpected position. An expected position would be the last
          known one when going from Paused to Playing, and 0 when going from
          Stopped to Playing.
        </p>
      </tp:docstring>
    </signal>

  </interface>
  <interface name="org.mpris.MediaPlayer2.Playlists">
    <tp:added version="2.1" />
    <tp:docstring>
      <p>Provides access to the media player's playlists.</p>
      <p>
        Since D-Bus does not provide an easy way to check for what interfaces
        are exported on an object, clients should attempt to get one of the
        properties on this interface to see if it is implemented.
      </p>
    </tp:docstring>

    <tp:simple-type name="Playlist_Id" type="o" array-name="Playlist_Id_List">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Unique playlist identifier.</p>
        <tp:rationale>
          <p>
            Multiple playlists may have the same name.
          </p>
          <p>
            This is a D-Bus object id as that is the definitive way to have
            unique identifiers on D-Bus.  It also allows for future optional
            expansions to the specification where tracks are exported to D-Bus
            with an interface similar to org.gnome.UPnP.MediaItem2.
          </p>
        </tp:rationale>
      </tp:docstring>
    </tp:simple-type>

    <tp:simple-type name="Uri" type="s" array-name="Uri_List">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A URI.</p>
      </tp:docstring>
    </tp:simple-type>

    <tp:struct name="Playlist" array-name="Playlist_List">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A data structure describing a playlist.</p>
      </tp:docstring>
      <tp:member type="o" tp:type="Playlist_Id" name="Id">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>A unique identifier for the playlist.</p>
          <p>This should remain the same if the playlist is renamed.</p>
        </tp:docstring>
      </tp:member>
      <tp:member type="s" name="Name">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The name of the playlist, typically given by the user.</p>
        </tp:docstring>
      </tp:member>
      <tp:member type="s" tp:type="Uri" name="Icon">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The URI of an (optional) icon.</p>
        </tp:docstring>
      </tp:member>
    </tp:struct>

    <tp:struct name="Maybe_Playlist">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A data structure describing a playlist, or nothing.</p>
        <tp:rationale>
          <p>
            D-Bus does not (at the time of writing) support a MAYBE type,
            so we are forced to invent our own.
          </p>
        </tp:rationale>
      </tp:docstring>
      <tp:member type="b" name="Valid">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Whether this structure refers to a valid playlist.</p>
        </tp:docstring>
      </tp:member>
      <tp:member type="(oss)" tp:type="Playlist" name="Playlist">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The playlist, providing Valid is true, otherwise undefined.</p>
          <p>
            When constructing this type, it should be noted that the playlist
            ID must be a valid object path, or D-Bus implementations may reject
            it.  This is true even when Valid is false.  It is suggested that
            "/" is used as the playlist ID in this case.
          </p>
        </tp:docstring>
      </tp:member>
    </tp:struct>

    <tp:enum name="Playlist_Ordering" array-name="Playlist_Ordering_List" type="s">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Specifies the ordering of returned playlists.</p>
      </tp:docstring>
      <tp:enumvalue suffix="Alphabetical" value="Alphabetical">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Alphabetical ordering by name, ascending.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="CreationDate" value="Created">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Ordering by creation date, oldest first.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="ModifiedDate" value="Modified">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Ordering by last modified date, oldest first.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="LastPlayDate" value="Played">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>Ordering by date of last playback, oldest first.</p>
        </tp:docstring>
      </tp:enumvalue>
      <tp:enumvalue suffix="UserDefined" value="User">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>A user-defined ordering.</p>
          <tp:rationale>
            <p>
              Some media players may allow users to order playlists as they
              wish.  This ordering allows playlists to be retreived in that
              order.
            </p>
          </tp:rationale>
        </tp:docstring>
      </tp:enumvalue>
    </tp:enum>

    <method name="ActivatePlaylist" tp:name-for-bindings="Activate_Playlist">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Starts playing the given playlist.
        </p>
        <p>
          Note that this must be implemented.  If the media player does not
          allow clients to change the playlist, it should not implement this
          interface at all.
        </p>
        <p>
          It is up to the media player whether this completely replaces the
          current tracklist, or whether it is merely inserted into the
          tracklist and the first track starts.  For example, if the media
          player is operating in a "jukebox" mode, it may just append the
          playlist to the list of upcoming tracks, and skip to the first
          track in the playlist.
        </p>
      </tp:docstring>
      <arg direction="in" name="PlaylistId" type="o">
        <tp:docstring>
          <p>The id of the playlist to activate.</p>
        </tp:docstring>
      </arg>
    </method>

    <method name="GetPlaylists" tp:name-for-bindings="Get_Playlists">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Gets a set of playlists.</p>
      </tp:docstring>
      <arg direction="in" name="Index" type="u">
        <tp:docstring>
          <p>The index of the first playlist to be fetched (according to the ordering).</p>
        </tp:docstring>
      </arg>
      <arg direction="in" name="MaxCount" type="u">
        <tp:docstring>
          <p>The maximum number of playlists to fetch.</p>
        </tp:docstring>
      </arg>
      <arg direction="in" name="Order" type="s" tp:type="Playlist_Ordering">
        <tp:docstring>
          <p>The ordering that should be used.</p>
        </tp:docstring>
      </arg>
      <arg direction="in" name="ReverseOrder" type="b">
        <tp:docstring>
          <p>Whether the order should be reversed.</p>
        </tp:docstring>
      </arg>
      <arg direction="out" name="Playlists" type="a(oss)" tp:type="Playlist[]">
        <tp:docstring>
          <p>A list of (at most MaxCount) playlists.</p>
        </tp:docstring>
      </arg>
    </method>

    <property name="PlaylistCount" type="u" tp:name-for-bindings="Playlist_Count" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The number of playlists available.
        </p>
      </tp:docstring>
    </property>

    <property name="Orderings" tp:name-for-bindings="Orderings" type="as" tp:type="Playlist_Ordering[]" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The available orderings.  At least one must be offered.
        </p>
        <tp:rationale>
          <p>
            Media players may not have access to all the data required for some
            orderings.  For example, creation times are not available on UNIX
            filesystems (don't let the ctime fool you!).  On the other hand,
            clients should have some way to get the "most recent" playlists.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="ActivePlaylist" type="(b(oss))" tp:name-for-bindings="Active_Playlist" tp:type="Maybe_Playlist" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The currently-active playlist.
        </p>
        <p>
          If there is no currently-active playlist, the structure's Valid field
          will be false, and the Playlist details are undefined.
        </p>
        <p>
          Note that this may not have a value even after ActivatePlaylist is
          called with a valid playlist id as ActivatePlaylist implementations
          have the option of simply inserting the contents of the playlist into
          the current tracklist.
        </p>
      </tp:docstring>
    </property>

    <signal name="PlaylistChanged" tp:name-for-bindings="Playlist_Changed">
      <arg name="Playlist" type="(oss)" tp:type="Playlist">
        <tp:docstring>
          The playlist which details have changed.
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Indicates that either the Name or Icon attribute of a
           playlist has changed.
        </p>
        <p>Client implementations should be aware that this signal
           may not be implemented.
        </p>
        <tp:rationale>
           Without this signal, media players have no way to notify clients
           of a change in the attributes of a playlist other than the active one
        </tp:rationale>
      </tp:docstring>
    </signal>

  </interface>
  <interface name="org.mpris.MediaPlayer2.TrackList">

    <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
      <p>
        Provides access to a short list of tracks which were recently played or
        will be played shortly.  This is intended to provide context to the
        currently-playing track, rather than giving complete access to the
        media player's playlist.
      </p>
      <p>
        Example use cases are the list of tracks from the same album as the
        currently playing song or the
        <a href="http://projects.gnome.org/rhythmbox/">Rhythmbox</a> play queue.
      </p>
      <p>
        Each track in the tracklist has a unique identifier.
        The intention is that this uniquely identifies the track within
        the scope of the tracklist. In particular, if a media item
        (a particular music file, say) occurs twice in the track list, each
        occurrence should have a different identifier. If a track is removed
        from the middle of the playlist, it should not affect the track ids
        of any other tracks in the tracklist.
      </p>
      <p>
        As a result, the traditional track identifiers of URLs and position
        in the playlist cannot be used. Any scheme which satisfies the
        uniqueness requirements is valid, as clients should not make any
        assumptions about the value of the track id beyond the fact
        that it is a unique identifier.
      </p>
      <p>
        Note that the (memory and processing) burden of implementing the
        TrackList interface and maintaining unique track ids for the
        playlist can be mitigated by only exposing a subset of the playlist when
        it is very long (the 20 or so tracks around the currently playing
        track, for example). This is a recommended practice as the tracklist
        interface is not designed to enable browsing through a large list of tracks,
        but rather to provide clients with context about the currently playing track.
      </p>
    </tp:docstring>

    <tp:mapping name="Metadata_Map" array-name="Metadata_Map_List">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A mapping from metadata attribute names to values.</p>
        <p>
          The <b>mpris:trackid</b> attribute must always be present, and must be
          of D-Bus type "o".  This contains a D-Bus path that uniquely identifies
          the track within the scope of the playlist.  There may or may not be
          an actual D-Bus object at that path; this specification says nothing
          about what interfaces such an object may implement.
        </p>
        <p>
          If the length of the track is known, it should be provided in the
          metadata property with the "mpris:length" key.  The length must be
          given in microseconds, and be represented as a signed 64-bit integer.
        </p>
        <p>
          If there is an image associated with the track, a URL for it may be
          provided using the "mpris:artUrl" key.  For other metadata, fields
          defined by the
          <a href="http://xesam.org/main/XesamOntology">Xesam ontology</a>
          should be used, prefixed by "xesam:".  See the
          <a href="http://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata">metadata page on the freedesktop.org wiki</a>
          for a list of common fields.
        </p>
        <p>
          Lists of strings should be passed using the array-of-string ("as")
          D-Bus type.  Dates should be passed as strings using the ISO 8601
          extended format (eg: 2007-04-29T14:35:51).  If the timezone is
          known, RFC 3339's internet profile should be used (eg:
          2007-04-29T14:35:51+02:00).
        </p>
      </tp:docstring>
      <tp:member type="s" name="Attribute">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>
            The name of the attribute; see the
            <a href="http://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata">metadata page</a>
            for guidelines on names to use.
          </p>
        </tp:docstring>
      </tp:member>
      <tp:member type="v" name="Value">
        <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
          <p>The value of the attribute, in the most appropriate format.</p>
        </tp:docstring>
      </tp:member>
    </tp:mapping>

    <tp:simple-type name="Uri" type="s">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A unique resource identifier.</p>
      </tp:docstring>
    </tp:simple-type>

    <method name="GetTracksMetadata" tp:name-for-bindings="Get_Tracks_Metadata">
      <arg direction="in" name="TrackIds" type="ao" tp:type="Track_Id[]">
        <tp:docstring>
          <p>The list of track ids for which metadata is requested.</p>
        </tp:docstring>
      </arg>
      <arg direction="out" type="aa{sv}" tp:type="Metadata_Map[]" name="Metadata">
        <tp:docstring>
          <p>Metadata of the set of tracks given as input.</p>
          <p>See the type documentation for more details.</p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Gets all the metadata available for a set of tracks.</p>
        <p>
          Each set of metadata must have a "mpris:trackid" entry at the very least,
          which contains a string that uniquely identifies this track within
          the scope of the tracklist.
        </p>
      </tp:docstring>
    </method>

    <method name="AddTrack" tp:name-for-bindings="Add_Track">
      <arg direction="in" type="s" tp:type="Uri" name="Uri">
        <tp:docstring>
          <p>
            The uri of the item to add. Its uri scheme should be an element of the
            <strong>org.mpris.MediaPlayer2.SupportedUriSchemes</strong>
            property and the mime-type should match one of the elements of the
            <strong>org.mpris.MediaPlayer2.SupportedMimeTypes</strong>
          </p>
        </tp:docstring>
      </arg>
      <arg direction="in" type="o" tp:type="Track_Id" name="AfterTrack">
        <tp:docstring>
          <p>
            The identifier of the track after which
            the new item should be inserted. The path
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            indicates that the track should be inserted at the
            start of the track list.
          </p>
        </tp:docstring>
      </arg>
      <arg direction="in" type="b" name="SetAsCurrent">
        <tp:docstring>
          <p>
            Whether the newly inserted track should be considered as
            the current track. Setting this to true has the same effect as
            calling GoTo afterwards.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Adds a URI in the TrackList.</p>
        <p>
          If the <tp:member-ref>CanEditTracks</tp:member-ref> property is false,
          this has no effect.
        </p>
        <p>
          Note: Clients should not assume that the track has been added at the
          time when this method returns. They should wait for a TrackAdded (or
          TrackListReplaced) signal.
        </p>
      </tp:docstring>
    </method>

    <method name="RemoveTrack" tp:name-for-bindings="Remove__Track">
      <arg direction="in" type="o" tp:type="Track_Id" name="TrackId">
        <tp:docstring>
          <p>Identifier of the track to be removed.</p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            is <em>not</em> a valid value for this argument.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Removes an item from the TrackList.</p>
        <p>If the track is not part of this tracklist, this has no effect.</p>
        <p>
          If the <tp:member-ref>CanEditTracks</tp:member-ref> property is false,
          this has no effect.
        </p>
        <p>
          Note: Clients should not assume that the track has been removed at the
          time when this method returns. They should wait for a TrackRemoved (or
          TrackListReplaced) signal.
        </p>
      </tp:docstring>
    </method>

    <method name="GoTo" tp:name-for-bindings="Go_To">
      <arg direction="in" type="o" tp:type="Track_Id" name="TrackId">
        <tp:docstring>
          <p>Identifier of the track to skip to.</p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            is <em>not</em> a valid value for this argument.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Skip to the specified TrackId.</p>
        <p>If the track is not part of this tracklist, this has no effect.</p>
        <p>
          If this object is not <strong>/org/mpris/MediaPlayer2</strong>,
          the current TrackList's tracks should be replaced with the contents of
          this TrackList, and the TrackListReplaced signal should be fired from
          <strong>/org/mpris/MediaPlayer2</strong>.
        </p>
      </tp:docstring>
    </method>

    <property name="Tracks" type="ao" tp:type="Track_Id[]" tp:name-for-bindings="Tracks" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="invalidates"/>
      <tp:docstring>
        <p>
          An array which contains the identifier of each track
          in the tracklist, in order.
        </p>
        <p>
          The <literal>org.freedesktop.DBus.Properties.PropertiesChanged</literal>
          signal is emited every time this property changes, but the signal
          message does not contain the new value.

          Client implementations should rather rely on the
          <tp:member-ref>TrackAdded</tp:member-ref>,
          <tp:member-ref>TrackRemoved</tp:member-ref> and
          <tp:member-ref>TrackListReplaced</tp:member-ref> signals to keep their
          representation of the tracklist up to date.
        </p>
      </tp:docstring>
    </property>

    <property name="CanEditTracks" type="b" tp:name-for-bindings="Can_Edit_Tracks" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          If <strong>false</strong>, calling
          <tp:member-ref>AddTrack</tp:member-ref> or
          <tp:member-ref>RemoveTrack</tp:member-ref> will have no effect,
          and may raise a NotSupported error.
        </p>
      </tp:docstring>
    </property>

    <signal name="TrackListReplaced" tp:name-for-bindings="Track_List_Replaced">
      <arg name="Tracks" type="ao" tp:type="Track_Id[]">
        <tp:docstring>
          <p>The new content of the tracklist.</p>
        </tp:docstring>
      </arg>
      <arg name="CurrentTrack" type="o" tp:type="Track_Id">
        <tp:docstring>
          <p>The identifier of the track to be considered as current.</p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            indicates that there is no current track.
          </p>
          <p>
            This should correspond to the <literal>mpris:trackid</literal> field of the
            Metadata property of the <literal>org.mpris.MediaPlayer2.Player</literal>
            interface.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Indicates that the entire tracklist has been replaced.</p>
        <p>
          It is left up to the implementation to decide when
          a change to the track list is invasive enough that
          this signal should be emitted instead of a series of
          TrackAdded and TrackRemoved signals.
        </p>
      </tp:docstring>
    </signal>

    <signal name="TrackAdded" tp:name-for-bindings="Track_Added">
      <arg type="a{sv}" tp:type="Metadata_Map" name="Metadata">
        <tp:docstring>
          <p>The metadata of the newly added item.</p>
          <p>This must include a mpris:trackid entry.</p>
          <p>See the type documentation for more details.</p>
        </tp:docstring>
      </arg>
      <arg type="o" tp:type="Track_Id" name="AfterTrack">
        <tp:docstring>
          <p>
            The identifier of the track after which the new track
            was inserted. The path
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            indicates that the track was inserted at the
            start of the track list.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Indicates that a track has been added to the track list.</p>
      </tp:docstring>
    </signal>

    <signal name="TrackRemoved" tp:name-for-bindings="Track_Removed">
      <arg type="o" tp:type="Track_Id" name="TrackId">
        <tp:docstring>
          <p>The identifier of the track being removed.</p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            is <em>not</em> a valid value for this argument.
          </p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Indicates that a track has been removed from the track list.</p>
      </tp:docstring>
    </signal>

    <signal name="TrackMetadataChanged" tp:name-for-bindings="Track_Metadata_Changed">
      <arg type="o" tp:type="Track_Id" name="TrackId">
        <tp:docstring>
          <p>The id of the track which metadata has changed.</p>
          <p>If the track id has changed, this will be the old value.</p>
          <p>
            <literal>/org/mpris/MediaPlayer2/TrackList/NoTrack</literal>
            is <em>not</em> a valid value for this argument.
          </p>
        </tp:docstring>
      </arg>
      <arg type="a{sv}" tp:type="Metadata_Map" name="Metadata">
        <tp:docstring>
          <p>The new track metadata.</p>
          <p>
            This must include a mpris:trackid entry.  If the track id has
            changed, this will be the new value.
          </p>
          <p>See the type documentation for more details.</p>
        </tp:docstring>
      </arg>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Indicates that the metadata of a track in the tracklist has changed.
        </p>
        <p>
          This may indicate that a track has been replaced, in which case the
          mpris:trackid metadata entry is different from the TrackId argument.
        </p>
      </tp:docstring>
    </signal>

  </interface>
  <interface name="org.mpris.MediaPlayer2">
    <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>

    <method name="Raise" tp:name-for-bindings="Raise">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Brings the media player's user interface to the front using any
          appropriate mechanism available.
        </p>
        <p>
          The media player may be unable to control how its user interface
          is displayed, or it may not have a graphical user interface at all.
          In this case, the <tp:member-ref>CanRaise</tp:member-ref> property is
          <strong>false</strong> and this method does nothing.
        </p>
      </tp:docstring>
    </method>

    <method name="Quit" tp:name-for-bindings="Quit">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Causes the media player to stop running.</p>
        <p>
          The media player may refuse to allow clients to shut it down.
          In this case, the <tp:member-ref>CanQuit</tp:member-ref> property is
          <strong>false</strong> and this method does nothing.
        </p>
        <p>
          Note: Media players which can be D-Bus activated, or for which there is
          no sensibly easy way to terminate a running instance (via the main
          interface or a notification area icon for example) should allow clients
          to use this method. Otherwise, it should not be needed.
        </p>
        <p>If the media player does not have a UI, this should be implemented.</p>
      </tp:docstring>
    </method>

    <property name="CanQuit" type="b" tp:name-for-bindings="Can_Quit" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          If <strong>false</strong>, calling
          <tp:member-ref>Quit</tp:member-ref> will have no effect, and may
          raise a NotSupported error.  If <strong>true</strong>, calling
          <tp:member-ref>Quit</tp:member-ref> will cause the media application
          to attempt to quit (although it may still be prevented from quitting
          by the user, for example).
        </p>
      </tp:docstring>
    </property>

    <property name="Fullscreen" type="b" tp:name-for-bindings="Fullscreen" access="readwrite">
      <tp:added version="2.2" />
      <annotation name="org.mpris.MediaPlayer2.property.optional" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>Whether the media player is occupying the fullscreen.</p>
        <p>
          This is typically used for videos.  A value of <strong>true</strong>
          indicates that the media player is taking up the full screen.
        </p>
        <p>
          Media centre software may well have this value fixed to <strong>true</strong>
        </p>
        <p>
          If <tp:member-ref>CanSetFullscreen</tp:member-ref> is <strong>true</strong>,
          clients may set this property to <strong>true</strong> to tell the media player
          to enter fullscreen mode, or to <strong>false</strong> to return to windowed
          mode.
        </p>
        <p>
          If <tp:member-ref>CanSetFullscreen</tp:member-ref> is <strong>false</strong>,
          then attempting to set this property should have no effect, and may raise
          an error.  However, even if it is <strong>true</strong>, the media player
          may still be unable to fulfil the request, in which case attempting to set
          this property will have no effect (but should not raise an error).
        </p>
        <tp:rationale>
          <p>
            This allows remote control interfaces, such as LIRC or mobile devices like
            phones, to control whether a video is shown in fullscreen.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanSetFullscreen" type="b" tp:name-for-bindings="Can_Set_Fullscreen" access="read">
      <tp:added version="2.2" />
      <annotation name="org.mpris.MediaPlayer2.property.optional" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          If <strong>false</strong>, attempting to set
          <tp:member-ref>Fullscreen</tp:member-ref> will have no effect, and may
          raise an error.  If <strong>true</strong>, attempting to set
          <tp:member-ref>Fullscreen</tp:member-ref> will not raise an error, and (if it
          is different from the current value) will cause the media player to attempt to
          enter or exit fullscreen mode.
        </p>
        <p>
          Note that the media player may be unable to fulfil the request.
          In this case, the value will not change.  If the media player knows in
          advance that it will not be able to fulfil the request, however, this
          property should be <strong>false</strong>.
        </p>
        <tp:rationale>
          <p>
            This allows clients to choose whether to display controls for entering
            or exiting fullscreen mode.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="CanRaise" type="b" tp:name-for-bindings="Can_Raise" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          If <strong>false</strong>, calling
          <tp:member-ref>Raise</tp:member-ref> will have no effect, and may
          raise a NotSupported error.  If <strong>true</strong>, calling
          <tp:member-ref>Raise</tp:member-ref> will cause the media application
          to attempt to bring its user interface to the front, although it may
          be prevented from doing so (by the window manager, for example).
        </p>
      </tp:docstring>
    </property>

    <property name="HasTrackList" type="b" tp:name-for-bindings="Has_TrackList" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          Indicates whether the <strong>/org/mpris/MediaPlayer2</strong>
          object implements the <strong>org.mpris.MediaPlayer2.TrackList</strong>
          interface.
        </p>
      </tp:docstring>
    </property>

    <property name="Identity" type="s" tp:name-for-bindings="Identity" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>A friendly name to identify the media player to users.</p>
        <p>This should usually match the name found in .desktop files</p>
        <p>(eg: "VLC media player").</p>
      </tp:docstring>
    </property>

    <property name="DesktopEntry" type="s" tp:name-for-bindings="Desktop_Entry" access="read">
      <annotation name="org.mpris.MediaPlayer2.property.optional" value="true"/>
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>The basename of an installed .desktop file which complies with the <a href="http://standards.freedesktop.org/desktop-entry-spec/latest/">Desktop entry specification</a>,
        with the ".desktop" extension stripped.</p>
        <p>
          Example: The desktop entry file is "/usr/share/applications/vlc.desktop",
          and this property contains "vlc"
        </p>
      </tp:docstring>
    </property>

    <property name="SupportedUriSchemes" type="as" tp:name-for-bindings="Supported_Uri_Schemes" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The URI schemes supported by the media player.
        </p>
        <p>
          This can be viewed as protocols supported by the player in almost
          all cases.  Almost every media player will include support for the
          "file" scheme.  Other common schemes are "http" and "rtsp".
        </p>
        <p>
          Note that URI schemes should be lower-case.
        </p>
        <tp:rationale>
          <p>
            This is important for clients to know when using the editing
            capabilities of the Playlist interface, for example.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

    <property name="SupportedMimeTypes" type="as" tp:name-for-bindings="Supported_Mime_Types" access="read">
      <tp:docstring xmlns="http://www.w3.org/1999/xhtml">
        <p>
          The mime-types supported by the media player.
        </p>
        <p>
          Mime-types should be in the standard format (eg: audio/mpeg or
          application/ogg).
        </p>
        <tp:rationale>
          <p>
            This is important for clients to know when using the editing
            capabilities of the Playlist interface, for example.
          </p>
        </tp:rationale>
      </tp:docstring>
    </property>

  </interface>
</node>
"""
mpris_node = gi.repository.Gio.DBusNodeInfo.new_for_xml(mpris_xml)


class YukiData:
    callback = None
    get_options = None
    mpris_bus = None


def mpris_handle_method_call(
    connection, sender, object_path, interface_name, method_name, params, invocation
):
    logger.debug(
        f"object_path = {object_path} interface_name = {interface_name} "
        f"method_name = {method_name} params = {params.unpack()}"
    )
    if interface_name == "org.freedesktop.DBus.Properties" and method_name == "Get":
        invocation.return_value(
            gi.repository.GLib.Variant.new_tuple(
                gi.repository.GLib.Variant(
                    "v",
                    YukiData.get_options()[params.unpack()[0]][params.unpack()[1]],
                )
            )
        )
    elif (
        interface_name == "org.freedesktop.DBus.Properties" and method_name == "GetAll"
    ):
        invocation.return_value(
            gi.repository.GLib.Variant.new_tuple(
                gi.repository.GLib.Variant(
                    "a{sv}", YukiData.get_options()[params.unpack()[0]]
                )
            )
        )
    else:
        invocation.return_value(
            YukiData.callback((interface_name, method_name, params))
        )


def mpris_on_bus_acquired(connection, name):
    logger.debug(f"Bus acquired for name {name}")
    register_ids = []
    for interface in mpris_node.interfaces:
        # TODO implement TrackList interface
        if interface.name != "org.mpris.MediaPlayer2.TrackList":
            logger.debug(f"Registering {interface.name}")
            register_ids.append(
                connection.register_object(
                    "/org/mpris/MediaPlayer2",
                    interface,
                    mpris_handle_method_call,
                    None,
                    None,
                )
            )


def start_mpris(pid, callback, get_options):
    YukiData.callback = callback
    YukiData.get_options = get_options
    return gi.repository.Gio.bus_own_name(
        gi.repository.Gio.BusType.SESSION,
        f"org.mpris.MediaPlayer2.yuki_iptv.instance{pid}",
        gi.repository.Gio.BusNameOwnerFlags.NONE,
        mpris_on_bus_acquired,
        lambda _connection, name: logger.info(f"Name acquired: {name}"),
        lambda _connection, name: logger.warning(f"Lost connection to name {name}"),
    )


def emit_mpris_change(interface_name, variable):
    if YukiData.mpris_bus is None:
        try:
            YukiData.mpris_bus = gi.repository.Gio.bus_get_sync(
                gi.repository.Gio.BusType.SESSION, None
            )
        except Exception:
            pass
    try:
        YukiData.mpris_bus.emit_signal(
            None,
            "/org/mpris/MediaPlayer2",
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            gi.repository.GLib.Variant(
                "(sa{sv}as)",
                (
                    interface_name,
                    variable,
                    {},
                ),
            ),
        )
        # Clear memory
        variable = None
    except Exception:
        pass


def mpris_seeked(position):
    if YukiData.mpris_bus is None:
        try:
            YukiData.mpris_bus = gi.repository.Gio.bus_get_sync(
                gi.repository.Gio.BusType.SESSION, None
            )
        except Exception:
            pass
    try:
        YukiData.mpris_bus.emit_signal(
            None,
            "/org/mpris/MediaPlayer2",
            "org.mpris.MediaPlayer2.Player",
            "Seeked",
            gi.repository.GLib.Variant.new_tuple(
                gi.repository.GLib.Variant("x", position)
            ),
        )
    except Exception:
        pass
