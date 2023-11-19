# Railway automated announcement simulator

This is a little tool designed to simulate automated announcements as formerly
found at many railway stations across the South of England, and currently found
at a few in the North and many in Scotland.

Please note that this project is not affiliated with Realtime Trains, KeTech,
or any other company in the rail industry.

It uses the Realtime Trains API to fetch realtime data. Note that this API is
not perfectly suited for this purpose, due mostly to limitations in the source
data, and so some functionality that you might expect such as train formations,
catering information, and a few others things is missing. This is not something
I can do anything about unless either the RTT API starts providing this
information (which it mostly can't for technical reasons), or I switch to a
different API.

It is designed for use with sound files available from elsewhere, which include
Phil Sayer, Celia Drummond, and Alison McKay.

I have based announcement scripts mostly from memory with a bit of creative
licence here and there, with the odd use of real recordings online to get
details and timing right in a few places. However, I expect there to be errors,
and I absolutely welcome pull requests if you're able, or issues raised if
you're not. I really want to get this as accurate as possible in the long term!
While the files are from KeTech I most fondly remember the Amey systems, so
accuracy towards those is the primary target, but I am very happy to include
options to simulate other systems I might not have remembered or considered, as
long as the sound clips are available.

This script is still quite new and I expect a few bugs to still be present. If
you experience a crash or an announcement that sounds wrong, feel free to file
an issue (please include the output of the script if possible). However please
do check the configuration hints down below.

I'm afraid I've not made getting it set up particularly easy or friendly, so I
would rate this as only suitable for those comfortable with using a
command-line. If anyone wishes to package this up into a more user-friendly
format they are welcome to do so provided they comply with the terms of the
(very permissive) MIT licence, and I would kindly request they let me know they
are doing so.

## Setup instructions

* Sign up for the Realtime Trains Pull API at https://api.rtt.io/ and obtain
  an API key and password. Note you should *not* need to request the detailed
  API for this, as I don't believe I use any fields from it, but reports from
  those who have tested it are welcome.
* Ensure that you have Python (3.11 or newer) and git installed.
* Clone both this repository and the repository containing the sound files into
  a convenient location: 
```
git clone https://github.com/Muzer/rtt-announce
git clone https://github.com/Rail-Announcements/ketech-llpa-announcements
```
* Change into the directory of the repo containing the sound files.
* Modify the `rename_snippets.py` config section in your favourite text editor
  — change the `output_dir` (for instance, to `renamed_wavs/`) and change
  `filetype` to `wav`. Be sure to save it.
* Now, run `rename_snippets.py`, eg:
```
python rename_snippets.py
```
* ...this will create a directory containing wav files renamed appropriately
  for my announcement script.
* Now, edit the `rtt-announce.toml` file you cloned from this repository. Fill
  in the API key and password, and fill in the full path to your `renamed_wavs`
  directory you created above. Tweak any settings you might want to change.
* Install python dependencies (sorry, I have no idea how to package Python
  stuff nowadays):
```
pip install pyaudio requests soundfile
```
* Finally, you should be able to run the script:
```
python rtt-announce.py
```
* You can pass a different station as a command-line argument, but any other
  settings changes will need to be made in the config file.

Note that when the script starts running, there will often be a large "backlog"
of delay, cancellation, "now standing", and safety announcements to get
through. However at small to medium stations this will calm down fairly
quickly. At large stations it might take longer to "catch up" to the present
time; you may wish to consider disabling some announcements or parts of
announcements, or making delay announcements less frequent — see below.

## Configuration hints

* You can choose from voices "Male1" (Phil Sayer), "Female1" (Celia Drummond),
  and "Female2" (Alison McKay). Note that the latter has a lot of missing voice
  clips so features will be limited, and it will not work well at all at
  stations outside of Scotland.
* Almost all announcement types can be turned on or off individually. Don't
  like so many announcements about arrivals? Switch them off! Hate the safety
  announcements? They're gone too! Check out the `announcements_enabled`
  section for this.
* **Not hearing any announcements, or only hearing announcements for certain
  trains?** Check on the Realtime Trains website and see if these trains show
  as "Approaching", "Arriving", and "At Platform" at appropriate times. If not,
  it is likely that this area has been resignalled relatively recently and
  Realtime Trains does not yet have the new detailed timing information to
  produce this data. If this is the case, I suggest you try enabling
  `departures_trust_triggered` and `arrivals_trust_triggered` announcement
  types. This is a degraded mode of operation so the full functionality will
  not be available, but this will allow you to hear a single announcement which
  will be triggered whenever a train's arrival time or platform is confirmed.
* Announcements too long but don't want to turn any off entirely? Most
  announcements can be customised to reduce the length or frequency, and many
  iterations were once found across the rail network so a lot of variants will
  remain authentic. As an example, you can disable the calling pattern from any
  announcement, you can disable repetition of the introduction on "next train"
  announcements, you can reduce the frequency of delay announcements or disable
  new announcements whenever a train's delay changes, and many more.
* For demonstration purposes I have set up the default config file to have some
  features from both Southern and South Western stations. For instance from
  Southern land I have enabled "X, this is X" announcements for trains from
  elsewhere now standing at the platform, and I have enabled "train now
  standing" wording — but all of this can be customised and hopefully you
  should be able to easily craft announcements authentic to any region based
  solely on editing the config file. If there is an option you think is missing
  which would help you get closer to the authentic announcement style you
  remember, I will be happy to add it!
* By default announcements will not play if the train's destination is
  unavailable; however they will play if only a calling point is unavailable.
  This affects trains to places such as Tweedbank and Headbolt Lane. By default
  as well, if a sound clip (usually a calling point) is not found, it will
  repeat the previous sound clip — this is an authentic feature of the Amey
  system formerly used across the South.

## Roadmap

I am now reasonably happy with the way announcements sound and the general
script; however as mentioned above improvements and suggestions for
improvements or new features are always absolutely welcome!

While I think I've got the timing of announcements fairly good, there are still
some areas that don't quite sound right to me, and so I might in future do some
tweaking to adjust the length of the small pauses between snippets.

In future I would like to make a truly authentic system with configurable
channels of different voices for different platforms. If and when I perform
this revamp I also plan for it to include authentic features like unimportant
(eg safety) announcements being interrupted by train announcements, and then
restarting once the important announcement is done.
