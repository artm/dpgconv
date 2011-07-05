#! /usr/bin/python
# DPG Converter by Anton Romanov (c) 2006
# released under GPL-2
# 
"""A script to transcode video files to DPG format suitable for
   Nintendo DS (tm)
   
dpgconv.py /home/foo/blah.avi /home/foo/blah2.avi
command line options:
	-q,--hq
		high quality video
	-l,--lq
		low quality video(takes no effect when --hq,-q is set)]
	default is normal quality
	
	-v,--vbps xxx
		sets video stream bps in kb/s(default: 256)
	-a,--abps xxx
		sets audio stream bps kb/s (default: 128)
	-f,--fps xx
		sets video frames per second (default:15)
	-z,--hz
		sets audio frequency (default:32000)
	-c,--channels
		2 - stereo, 1 - mono
		default is to leave as is unless input audio channels
		number is bigger then 2 ... then default is stereo
	--height xxx
		destination video height
	--width xxx
		destination video width

	--mv
		additional parameters for mencoder for video

	--ma
		additional parameters for mencoder for audio
	
	Hardcoding subtitles
	--nosub
		do no try autoloading of subtitles
		(default is to try to load subtitle with matching filename)
	--sub,-s xxx
		Specify subtitles for hardcoding into video output
		(is obviously only usable if you specify one file at a time)
	--subcp xxx
		specify subtitles encoding
	--font xxx
		specify font for subtitles
  EXAMPLE:
    --font ~/arial-14/font.desc
    --font ~/arialuni.ttf
    --font 'Bitstream Vera Sans'

  You can specify font, subcp and other additional mencoder parameters in
	~/.mplayer/mencoder.conf
  EXAMPLE:
	font=/usr/local/share/fonts/msfonts/comic.ttf
	subcp=cp1251

"""
import sys, os, optparse
MP2TMP="mp2tmp.mp2"
MPGTMP="mpgtmp.mpg"
HEADERTMP="header.tmp"
#Print a help message if requested.
if "-h" in sys.argv or "-help" in sys.argv or "--help" in sys.argv:
	print __doc__
	raise SystemExit

def conv_vid(file):
	print "Transcoding video"
	if options.hq:
		v_cmd =  ( " -quiet \""+ file +"\" -v -ofps " + `options.fps` + " -sws 9 -vf scale=" + `options.width` + ":" + `options.height` +":::3 -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:mbd=2:trell:cbp:mv0:cmp=6:subcmp=6:precmp=6:dia=3:predia=3:last_pred=3:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo" )
	elif options.lq:
		v_cmd = ( " -quiet \"" + file + "\" -v -ofps " + `options.fps` + " -vf scale=" + `options.width` + ":" + `options.height` + " -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo" )
	else :
		v_cmd = ( " -quiet \""+ file +"\" -v -ofps " + `options.fps` + " -sws 9 -vf scale=" + `options.width` + ":" + `options.height` + ":::3 -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:mbd=2:trell:cbp:mv0:cmp=2:subcmp=2:precmp=2:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo")
	
	if options.nosub:
		if options.sub != None:
			v_cmd = " -sub \"" + options.sub + "\" " + v_cmd
	else:
		basename = os.path.splitext ( file )[0]
		if options.sub != None:
			v_cmd = " -sub \"" + options.sub + "\" " + v_cmd
		elif os.path.exists ( basename + ".srt" ):
			v_cmd = " -sub \"" + basename + ".srt" + "\" " + v_cmd
		elif os.path.exists ( basename + ".sub" ):
			v_cmd = " -sub \"" + basename + ".sub" + "\" " + v_cmd
		elif os.path.exists ( basename + ".ssa" ):
			v_cmd = " -sub \"" + basename + ".ssa" + "\" " + v_cmd
	
	if options.subcp != None:
		v_cmd = " -subcp " + options.subcp + v_cmd
	if options.font != None:
		v_cmd = " -font " + options.font + v_cmd

	v_cmd = "mencoder " + v_cmd

#	print  v_cmd

	v_out = commands.getoutput ( v_cmd )
	p = re.compile ("([0-9]*)( frames)")
	m = p.search( v_out )
	frames = m.group(1)
	print "Total frames:" + frames
	return frames

def conv_aud(file):
	print "Transcoding Audio"
	a_cmd = ( "mencoder -quiet \"" +file + "\" -v -of rawaudio -oac lavc -ovc copy -lavcopts acodec=mp2:abitrate=" + `options.abps` + " -o " + MP2TMP )
	identify = commands.getoutput( "mplayer -frames 0 -vo null -ao null -identify \"" + file + "\" | grep -E \"^ID|VIDEO|AUDIO\"")
	p = re.compile ("([0-9]*)( ch)")
	m = p.search( identify )
	if m:
		c = m.group(1)
		if options.channels == None:
			if c > 2:
				a_cmd = a_cmd + " -af channels=2,resample=" +`options.hz`+ ":1:2"
			else:
				a_cmd = a_cmd + " -af resample=" +`options.hz`+ ":1:2"
		elif options.channels >= 2:
			a_cmd = a_cmd + " -af channels=2,resample=" +`options.hz`+ ":1:2"
		else:
			a_cmd = a_cmd + " -af channels=1,resample=" +`options.hz`+ ":1:2"

	a_out = commands.getoutput ( a_cmd )

def write_header(frames):
	print "Creating header"
	audiostart=36
	audiosize = os.stat(MP2TMP)[stat.ST_SIZE]
	videosize = os.stat(MPGTMP)[stat.ST_SIZE]
	videostart = audiostart + audiosize
	videoend = videostart + videosize
	locationValues = [ int(audiostart), int(audiosize), int(videostart), int(videosize) ]
	f=open(HEADERTMP, 'wb')
	
	headerValues = [ "DPG0", int(frames), options.fps, 0, options.hz , 0 ]
	
	f.write (struct.pack( "4s" , headerValues[0]))
	f.write (struct.pack ( "<l" , headerValues[1]))
	f.write (struct.pack ( ">h" , headerValues[2]))
	f.write (struct.pack ( ">h" , headerValues[3]))
	f.write (struct.pack ( "<l" , headerValues[4]))
	f.write (struct.pack ( "<l" , headerValues[5]))

	f.write (struct.pack ( "<l" ,locationValues[0]))
	f.write (struct.pack ( "<l" ,locationValues[1]))
	f.write (struct.pack ( "<l" ,locationValues[2]))
	f.write (struct.pack ( "<l" ,locationValues[3]))
	f.close()

def conv_file(file):
	print "Converting " + file
	frames = conv_vid (file)
	conv_aud(file)
	write_header(frames)
	dpgname = os.path.basename ( os.path.splitext ( file )[0] ) + ".dpg"
	
	print "Creating " + dpgname
	commands.getoutput( "cat \"" + HEADERTMP + "\" \"" + MP2TMP + "\" \"" + MPGTMP + "\" > \"" + dpgname + "\"")
	print "Removing temporary files"
	os.unlink ( MPGTMP )
	os.unlink ( MP2TMP )
	os.unlink ( HEADERTMP )
	print "Done converting \"" + file + "\" to \"" + dpgname + "\""



from optparse import OptionParser
parser = OptionParser()
parser.add_option("-f","--fps", type="int", dest="fps" , default=15)
parser.add_option("-q","--hq",action="store_true", dest="hq", default=False)
parser.add_option("-l","--lq",action="store_true", dest="lq", default=False)
parser.add_option("-v","--vbps", type="int", dest="vbps", default=256)
parser.add_option("-a","--abps", type="int", dest="abps", default=128)
parser.add_option("--height", type="int", dest="height", default=192)
parser.add_option("--width", type="int", dest="width", default=256)
parser.add_option("-z","--hz", type="int", dest="hz", default=32000)
parser.add_option("-c","--channels", type="int", dest="channels")
parser.add_option("--subcp", dest="subcp")
parser.add_option("-s","--sub", dest="sub")
parser.add_option("--font", dest="font")
parser.add_option("--mv", dest="mv")
parser.add_option("--ma", dest="ma")
parser.add_option("--nosub",action="store_true", dest="nosub", default=False)

(options, args) = parser.parse_args()

#print (options)
import commands,re,stat,struct
for file in args:
	conv_file(file)
