#!/usr/bin/env python
# -*- coding: utf-8-*-
#
# DPG Converter for linux
# released under GPL-2
# 
"""A script to transcode video files to DPG format suitable for
   Nintendo DS (tm)
   
dpgconv.py file1 file2 file3 ... fileN
command line options:
	--dpg
		0,1,2,3,4 sets DPG version.. default is DPG4
	
	--pf
		sets pixel format, default is 3
		0        RGB15
		1        RGB18
		2        RGB21
		3        RGB24 

	-2,--tp 
		extra high quality 2-pass encoded video
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
	--aid n
		use audio track n
	--volnorm
		normalize volume
	
	--height xxx
		destination video height (default: 192)
	--width xxx
		destination video width (default: 256)
	--keep-aspect
		try to keep aspect ratio
	
	NOTE:	width/height have no effect when --keep-aspect is set
	
	--mv
		additional parameters for mencoder for video

	--ma
		additional parameters for mencoder for audio

	Video Thumbnail
	--thumb xxx
		you can use this option if you convert only one video, or if
		you want the same preview for all videos.
		thumbnails are only in DPG4 videos.
		all formats supported by python imaging library can be used.
		the image will be resized and converted automically.
		
		NOTE: thumbnail will be generated autimatically
		from input video if you won't set this parameter

	Hardcoding subtitles
	--nosub
		do no try autoloading of subtitles
		(default is to try to load subtitle with matching filename)
	--sub,-s xxx
		Specify subtitles for hardcoding into video output
		(is obviously only usable if you specify one file at a time)
	--sid n
		use subtitle track n
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
from PIL import Image
import tempfile
from optparse import OptionParser
import signal
import commands,re,stat,struct,subprocess

MP2TMP="mp2tmp.mp2"
MPGTMP="mpgtmp.mpg"
HEADERTMP="header.tmp"
GOPTMP="gop.tmp"
STATTMP="stat.tmp"
THUMBTMP="thumb.tmp"

MENCODER="mencoder"
MPLAYER="mplayer"
MPEG_STAT="mpeg_stat"




#Print a help message if requested.
if "-h" in sys.argv or "-help" in sys.argv or "--help" in sys.argv:
	print __doc__
	raise SystemExit

def cleanup_callback(a,b):
	print "Removing temporary files"
	if os.path.lexists ( MPGTMP ):
		os.unlink ( MPGTMP )
	if os.path.lexists ( MP2TMP ):
		os.unlink ( MP2TMP )
	if os.path.lexists ( HEADERTMP ):
		os.unlink ( HEADERTMP )
	if os.path.lexists ( GOPTMP ):
		os.unlink ( GOPTMP )
	if os.path.lexists ( STATTMP ):
		os.unlink ( STATTMP )
	if os.path.lexists ( THUMBTMP ):
		os.unlink ( THUMBTMP )
	if os.path.lexists ( SHOTTMP ):
		os.rmdir ( SHOTTMP )

def conv_vid(file):
	if ((options.dpg == 0) | (options.dpg == 4)):
		v_pf = "format=rgb24,"
		options.pf = 3
	elif options.pf == 3:
		v_pf = "format=rgb24,"
	elif options.pf == 2:
		v_pf = "format=rgb21,"
	elif options.pf == 1:
		v_pf = "format=rgb18,"
	elif options.pf == 0:
		v_pf = "format=fmt=rgb15,"
	else:
		v_pf = "format=rgb24,"
		options.pf = 3

	if options.aspect:
		aspect = commands.getoutput( MPLAYER + " -frames 1 -vo null -ao null -identify \"" + file + "\" | grep -E \"^ID_VIDEO_ASPECT\" | tail -1")
		p = re.compile ("ID_VIDEO_ASPECT=(.*)")
		m = p.search( aspect )
		if m:
			print "Aspect ratio = %s" % m.group(1)
			ar = float(m.group(1))
			if int(256.0/ar) <= 192:
				options.width=256
				options.height=int(256.0/ar)
			else:
				options.height=192
				options.width=int(ar*192.0)
			print "Target size set to %dx%d." % (options.width,options.height)

	if options.tp:
		if options.fps < 24:
			print "mencoder won't work with double pass and fps < 24, forcing fps = 24"
			options.fps = 24
		v_cmd =  ( " \""+ file +"\" -v -ofps " + `options.fps` + " -sws 9 -vf " + v_pf + "scale=" + `options.width` + ":" + `options.height` +":::3,harddup -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:mbd=2:trell:cbp:mv0:vmax_b_frames=2:cmp=6:subcmp=6:precmp=6:dia=4:predia=4:bidir_refine=4:mv0_threshold=0:last_pred=3:vbitrate=" + `options.vbps` )
	elif options.hq:
		v_cmd =  ( " \""+ file +"\" -v -ofps " + `options.fps` + " -sws 9 -vf " + v_pf + "scale=" + `options.width` + ":" + `options.height` +":::3,harddup -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:mbd=2:trell:cbp:mv0:cmp=6:subcmp=6:precmp=6:dia=3:predia=3:last_pred=3:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo" )
	elif options.lq:
		v_cmd = ( " \"" + file + "\" -v -ofps " + `options.fps` + " -vf " + v_pf + "scale=" + `options.width` + ":" + `options.height` + ",harddup -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo" )
	else :
		v_cmd = ( " \""+ file +"\" -v -ofps " + `options.fps` + " -sws 9 -vf " + v_pf + "scale=" + `options.width` + ":" + `options.height` + ":::3,harddup -nosound -ovc lavc -lavcopts vcodec=mpeg1video:vstrict=-2:mbd=2:trell:cbp:mv0:cmp=2:subcmp=2:precmp=2:vbitrate=" + `options.vbps` + " -o " + MPGTMP + " -of rawvideo")
	
	if options.nosub:
		if options.sub != None:
			v_cmd = " -sub \"" + options.sub + "\" " + v_cmd
	else:
		basename = os.path.splitext ( file )[0]
		if options.sid != None:
			v_cmd = " -sid \"" + str(options.sid) + "\" " + v_cmd
		if options.sub != None:
			v_cmd = " -sub \"" + options.sub + "\" " + v_cmd
		elif os.path.exists ( basename + ".ass" ):
			v_cmd = " -sub \"" + basename + ".ass" + "\" " + v_cmd
		elif os.path.exists ( basename + ".srt" ):
			v_cmd = " -sub \"" + basename + ".srt" + "\" " + v_cmd
		elif os.path.exists ( basename + ".sub" ):
			v_cmd = " -sub \"" + basename + ".sub" + "\" " + v_cmd
		elif os.path.exists ( basename + ".ssa" ):
			v_cmd = " -sub \"" + basename + ".ssa" + "\" " + v_cmd
	
	if options.subcp != None:
		v_cmd = " -subcp " + options.subcp + v_cmd
	if options.font != None:
		v_cmd = " -font \"" + options.font + "\"" + v_cmd

	v_cmd = MENCODER + " " + v_cmd
	if options.tp:
		v_cmd_two = v_cmd
		v_cmd = v_cmd + ":vpass=1:turbo:vb_strategy=2:vrc_maxrate=500:vrc_minrate=0:vrc_buf_size=327:intra_matrix=8,9,12,22,26,27,29,34,9,10,14,26,27,29,34,37,12,14,18,27,29,34,37,38,22,26,27,31,36,37,38,40,26,27,29,36,39,38,40,48,27,29,34,37,38,40,48,58,29,34,37,38,40,48,58,69,34,37,38,40,48,58,69,79:inter_matrix=16,18,20,22,24,26,28,30,18,20,22,24,26,28,30,32,20,22,24,26,28,30,32,34,22,24,26,30,32,32,34,36,24,26,28,32,34,34,36,38,26,28,30,32,34,36,38,40,28,30,32,34,36,38,42,42,30,32,34,36,38,40,42,44" + " -o " + MPGTMP + " -of rawvideo"
		v_cmd_two = v_cmd_two + ":vpass=2:vrc_maxrate=500:vrc_minrate=0:vrc_buf_size=327:keyint=60:intra_matrix=8,9,12,22,26,27,29,34,9,10,14,26,27,29,34,37,12,14,18,27,29,34,37,38,22,26,27,31,36,37,38,40,26,27,29,36,39,38,40,48,27,29,34,37,38,40,48,58,29,34,37,38,40,48,58,69,34,37,38,40,48,58,69,79:inter_matrix=16,18,20,22,24,26,28,30,18,20,22,24,26,28,30,32,20,22,24,26,28,30,32,34,22,24,26,30,32,32,34,36,24,26,28,32,34,34,36,38,26,28,30,32,34,36,38,40,28,30,32,34,36,38,42,42,30,32,34,36,38,40,42,44" + " -o " + MPGTMP + " -of rawvideo"
		v_cmd_two = v_cmd_two + " " + options.mv
		v_cmd = v_cmd + " " + options.mv
	else:
		v_cmd = v_cmd + " " + options.mv
	#print v_cmd
	#print v_cmd_two
	proc = subprocess.Popen(v_cmd,shell=True,stdout=subprocess.PIPE,universal_newlines=True,stderr=open('/dev/null', 'w'))
	
	p = re.compile ("f (\(.*%\))")
	for line in proc.stdout:
		m = p.search( line )
		#print line
		if m:
			print "Transcoding video: " + m.group(1) + "\r" ,
	print "Transcoding video:   done"
	if options.tp:
		proc = subprocess.Popen(v_cmd_two,shell=True,stdout=subprocess.PIPE,universal_newlines=True,stderr=open('/dev/null', 'w'))
		for line in proc.stdout:
			m = p.search( line )
		
			if m:
				print "Transcoding video, pass 2: " + m.group(1) + "\r" ,
		print "Transcoding video, pass 2:   done"


def conv_aud(file):
	vol=''
	if options.volnorm:
		vol="-af volnorm"

	a_cmd = ( MENCODER + " \"" +file + "\" -v -of rawaudio -oac lavc -ovc copy -lavcopts acodec=mp2:abitrate=" + `options.abps` +" -o " + MP2TMP + " "+vol)
	identify = commands.getoutput( MPLAYER + " -frames 0 -vo null -ao null -identify \"" + file + "\" | grep -E \"^ID|VIDEO|AUDIO\"")
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
	else:
		print "Error running mplayer:"
		print identify

	if options.aid != None:
		a_cmd = a_cmd + " -aid " + str(options.aid)

	a_cmd = a_cmd + " " + options.ma
	#print a_cmd

	proc = subprocess.Popen(a_cmd,shell=True,stdout=subprocess.PIPE,universal_newlines=True,stderr=subprocess.STDOUT)

	v_out = ""
	
	p = re.compile ("f (\(.*%\))")
	for line in proc.stdout:
		m = p.search( line )
		if m:
			print "Transcoding audio: " + m.group(1) + "\r" ,
	print "Transcoding audio:   done"

def write_header(frames):
	print "Creating header"

	audiostart=36
	if options.dpg == 1:
		audiostart += 4
	elif (options.dpg == 2) | (options.dpg == 3):
		audiostart += 12
	elif options.dpg == 4:
		audiostart += 98320
	audiosize = os.stat(MP2TMP)[stat.ST_SIZE]
	videosize = os.stat(MPGTMP)[stat.ST_SIZE]
	videostart = audiostart + audiosize
	videoend = videostart + videosize
	f=open(HEADERTMP, 'wb')
	DPG = "DPG" + `options.dpg`
	headerValues = [ DPG, int(frames), options.fps, 0, options.hz , 0 ,int(audiostart), int(audiosize), int(videostart), int(videosize) ]
	
	f.write (struct.pack( "4s" , headerValues[0]))
	f.write (struct.pack ( "<l" , headerValues[1]))
	f.write (struct.pack ( ">h" , headerValues[2]))
	f.write (struct.pack ( ">h" , headerValues[3]))
	f.write (struct.pack ( "<l" , headerValues[4]))
	f.write (struct.pack ( "<l" , headerValues[5]))
	f.write (struct.pack ( "<l" , headerValues[6]))
	f.write (struct.pack ( "<l" , headerValues[7]))
	f.write (struct.pack ( "<l" , headerValues[8]))
	f.write (struct.pack ( "<l" , headerValues[9]))
	if options.dpg >= 2:
		gopsize = os.stat(GOPTMP)[stat.ST_SIZE]
		f.write (struct.pack ( "<l" , videoend ))
		f.write (struct.pack ( "<l" , gopsize))
	#sure !? and DPG3 ?
	if options.dpg != 1:
		f.write (struct.pack ( "<l" , options.pf ))
	if options.dpg == 4:
		f.write (struct.pack ( "4s" , "THM0"))
	f.close()

def mpeg_stat():
	p = re.compile ("frames: ([0-9]*)\.")
	s_out = commands.getoutput( MPEG_STAT + " -offset " + STATTMP + " " + MPGTMP )
	m = p.search( s_out )
	if m:
		frames = m.group(1)
		if options.dpg >= 2:
			gop=open(GOPTMP, 'wb')
			stat=open(STATTMP, 'rb')
			frame = 0
			for line in stat:
				sline = line.split()
				if sline[0] == "picture" :
					frame += 1
				elif sline[0] == "sequence":
					gop.write (struct.pack ( "<l" , frame ))
					gop.write (struct.pack ( "<l" , int(sline[1])/8 )) # mpeg_stat shows bit offsets
			gop.close()
			stat.close()
	else:
		print s_out
		return 0
	return frames

def conv_file(file):
	if not (os.path.lexists ( file )):
		print "File " + file + " doesn't exist"
	print "Converting " + file
	conv_vid (file)
	conv_aud(file)
	frames = mpeg_stat()
	if frames == 0:
		print "Error using mpeg_stat ... see error above"
		cleanup_callback (0,0)
		return
	if options.dpg == 4:
		conv_thumb(options.thumb,frames)
	write_header(frames)
	dpgname = os.path.basename ( os.path.splitext ( file )[0] ) + ".dpg"
	
	print "Creating " + dpgname
	#commands.getoutput( "cat \"" + HEADERTMP + "\" \"" + MP2TMP + "\" \"" + MPGTMP + "\" > \"" + dpgname + "\"")
	
	if options.dpg == 4:
		concat(dpgname,HEADERTMP,THUMBTMP,MP2TMP,MPGTMP,GOPTMP)
	elif (options.dpg == 2) | (options.dpg == 3):
		#commands.getoutput( "cat \"" + GOPTMP + "\" >> \"" + dpgname + "\"")
		concat(dpgname,HEADERTMP,MP2TMP,MPGTMP,GOPTMP)
	else:
		concat(dpgname,HEADERTMP,MP2TMP,MPGTMP)
	
	cleanup_callback (0,0)
	print "Done converting \"" + file + "\" to \"" + dpgname + "\""

def conv_thumb(file, frames):
	"""Converts PIL internal (24 or 32bit per pixel RGB) image
  	to 16 bit per pixel thumbnail.
	Takes a PNG screenshot if no file given.
	"""
	shot_file = None
	if not (os.path.lexists ( file )):
		print "Preview file will be generated from video file."
		shot_file = SHOTTMP +"/00000001.png"
		s_cmd = '%s %s -nosound -vo png:outdir=%s -frames 1 -ss %d' % (
			MPLAYER, MPGTMP, SHOTTMP, 
			int((int(frames)/options.fps)/10))
		output = commands.getoutput(s_cmd)
		#check for "Exiting... (End of file)" ?
		file = shot_file
	
	im = Image.open(file)
	width, height = im.size
	size = (256, 192)
	dest_w, dest_h = size

	if (width*dest_h<height*dest_w):
		matrix=[ height/dest_h, 0.0, -(dest_w -(width*dest_h/height))//2,
				0.0, height/dest_h, 0.0 ]
	else:
		matrix=[ width/dest_w, 0.0, 0.0,
				0.0, width/dest_w, -(dest_h -(height*dest_w/width))//2 ]	
	thumbim = im.transform(size, Image.AFFINE, matrix , Image.BICUBIC).getdata()

	data = list()
	for i in xrange(dest_h):
		row = list()
		for j in xrange(dest_w):
			red, green, blue = thumbim[i*dest_w+j][0], thumbim[i*dest_w+j][1], thumbim[i*dest_w+j][2]
			pixel = (( 1 << 15)
				| ((blue >> 3) << 10)
				| ((green >> 3) << 5)
				| (red >> 3))
			row.append(pixel)
		data.append(row)
	row_fmt=('H'*dest_w)
	thumb_data = ''.join(struct.pack(row_fmt, *row) for row in data)

	thumb_file=open(THUMBTMP, 'wb')
	thumb_file.write(thumb_data)
	thumb_file.close()
	#to create a file readable by an image viewer:
	#tga16_file = open('thumb.tga', 'wb')
	#tga_header='\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xC0\x00\x10\x00'
	#tga16_file.write(tga_header)
	#tga16_file.write(thumb_data)
	#tga16_file.close()

	#must be sure shot_file is always named 00000001.png
	#for batch processing
	if ( shot_file != None ):
		if (os.path.lexists ( shot_file )):
			os.unlink ( shot_file )

def init_names():
	global MPGTMP,MP2TMP,HEADERTMP,GOPTMP,STATTMP,THUMBTMP,SHOTTMP
	a,MP2TMP=tempfile.mkstemp()
	os.close(a)
	a,MPGTMP=tempfile.mkstemp()
	os.close(a)
	a,HEADERTMP=tempfile.mkstemp()
	os.close(a)
	a,GOPTMP=tempfile.mkstemp()
	os.close(a)
	a,STATTMP=tempfile.mkstemp()
	os.close(a)
	a,THUMBTMP=tempfile.mkstemp()
	os.close(a)
	SHOTTMP=tempfile.mkdtemp()

def concat(out,*files):
	outfile = open(out,'w')
	for name in files:
		outfile.write( open(name).read() )
	outfile.close()



parser = OptionParser()
parser.add_option("-f","--fps", type="int", dest="fps" , default=15)
parser.add_option("-q","--hq", action="store_true", dest="hq", default=False)
parser.add_option("-l","--lq", action="store_true", dest="lq", default=False)
parser.add_option("-v","--vbps", type="int", dest="vbps", default=256)
parser.add_option("-a","--abps", type="int", dest="abps", default=128)
parser.add_option("--volnorm", action="store_true", dest="volnorm", default=False)
parser.add_option("--keep-aspect", action="store_true", dest="aspect", default=False)
parser.add_option("--height", type="int", dest="height", default=192)
parser.add_option("--width", type="int", dest="width", default=256)
parser.add_option("-z","--hz", type="int", dest="hz", default=32000)
parser.add_option("-c","--channels", type="int", dest="channels")
parser.add_option("--subcp", dest="subcp")
parser.add_option("-s","--sub", dest="sub")
parser.add_option("--font", dest="font")
parser.add_option("--mv", dest="mv", default="")
parser.add_option("--ma", dest="ma", default="")
parser.add_option("-t", "--thumb", dest="thumb", default="")
parser.add_option("--nosub", action="store_true", dest="nosub", default=False)
parser.add_option("--dpg", type="int" , dest="dpg", default=4)
parser.add_option("--pf", type="int" , dest="pf", default=3)
parser.add_option("--sid", type="int" , dest="sid")
parser.add_option("--aid", type="int" , dest="aid")
parser.add_option("-2","--tp",action="store_true", dest="tp", default=False)
(options, args) = parser.parse_args()

signal.signal(signal.SIGINT, cleanup_callback)
signal.signal(signal.SIGTERM, cleanup_callback)

if options.dpg > 4:
	options.dpg = 2
if options.dpg < 0:
	options.dpg = 2

test = commands.getoutput ( MPEG_STAT + " --" )
m = re.compile ("mpeg_stat --(.*)").search(test)
if m:
	print m.group(0)
else:
	print "Error:"
	print test
	exit (0)
test = commands.getoutput ( MPLAYER )
m = re.compile ("^MPlayer.*").search(test)
if m:
	print m.group(0)
else:
	print "Error:"
	print test
	exit (0)
test = commands.getoutput ( MENCODER)
m = re.compile ("^MEncoder.*").search(test)
if m:
	print m.group(0)
else:
	print "Error:"
	print test
	exit (0)
print "It seems we found all programs :)...continuing"
print "______________________________________________"
init_names()
for file in args:
	conv_file(file)
