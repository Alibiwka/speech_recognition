#! /usr/bin/env python
#This program ROVERS a set of ASR hypotheses to get a superior result.
#Run in isolation, it generates fake data and measures the accuracy gain.
#Called from ca.py, it runs on real data from CAs.
#See ./notes for details on ROVER.  View with 4-space tabs.

import sys
import random
import os
SCRATCH='./temp'		#Temporary folder
#SCLITE='./sctk-2.4.10/bin/sclite'	#SCLITE
#ROVER='./sctk-2.4.10/bin/rover'	#ROVER
SCLITE='/home/alibi/Desktop/Work/AI_labs/Tools/rover/sctk-2.4.10/bin/sclite'	#SCLITE
ROVER='/home/alibi/Desktop/Work/AI_labs/Tools/rover/sctk-2.4.10/bin/rover'	#ROVER

def runsclite(gold,asrtext,folder=SCRATCH):
	'''Run NIST sclite to score a list of one or more
		hypotheses (asrtext) against ground truth (gold).
		Use folder as a place to store temporary files.
	'''
	#Create folder to store hypothesis files for sclite.exe:
	print 'folder=',folder
	if not os.path.exists(folder):
		os.makedirs(folder)
	returnpath = os.getcwd()
	os.chdir(folder)
	ref = open('ref.txt','w') #File with ground truth (reference)
	hyp = open('hyp.txt','w') #File with hypotheses (ASR output)
	print 'gold=',gold[0][:-1]
	for NH,hh in enumerate(asrtext):
		print 'NH=',NH,' hh=',hh
		ref.write(gold[0][:-1]+' (spk1_'+str(NH)+')\n')	#Write truth line
		hyp.write(hh+' (spk1_'+str(NH)+')\n')		#Write hypothesis line
	ref.close()
	hyp.close()
	#Run sclite.exe:
	returncode=os.system(SCLITE+' -r ref.txt -h hyp.txt -i rm -o sum pra')
	if returncode != 0:
		print 'Sclite returncode error=',returncode
		sys.exit()
	##Print results to screen:
	#print '____________________________________'
	#os.system('head -30 hyp.txt.sys')
	#print '____________________________________'
	#os.system('head -30 hyp.txt.pra')
	#Extract accuracy percentage from the "sys" output:
	os.system('grep spk1 hyp.txt.sys > sclite_result')
	fid = open('sclite_result','rU')
	#sclite_result = fid.readlines().split('|')[3]
	sclite_result = fid.readlines()[0].replace('|',' ')
	sclite_result = float(sclite_result.split()[3])
	os.chdir(returnpath)	#Go back to the previous folder
	return sclite_result

def runrover(asrtext,folder=SCRATCH):
	'''Combine multiple corrupted transcripts of a test phrase
		into a single, high-accuracy version.
		asrtext is a list of strings, each representing a hypothesis.
		folder is a directory to store temporary files for rover.exe.
	'''
	if len(asrtext) > 50:
		print 'rover.exe returns error 256 if you input > 50 hypotheses.'
		sys.exit()
	#Create folder to store hypothesis files for rover.exe:
	if not os.path.exists(folder):
		os.makedirs(folder)
	returnpath = os.getcwd()
	os.chdir(folder)
	#Create hypothesis files
	for NH,hh in enumerate(asrtext):
		f=open(str(NH),'w')
		hhsplit = hh.split(' ')	#Turn phrase into a list of words
		#Write a hypothesis file in the format expected by rover.exe:
		f.write('\n'.join('orig a 0.0 0.0 '+str(hh) for hh in hhsplit))
		f.close()
	NH += 1	#Convert last hypothesis number to number of hypotheses
	#Construct a command line for rover.exe
	com=ROVER
	for jj in range(NH):	#For each hypothesis file
		com += ' -h ' + str(jj) + ' ctm'
	com += ' -m meth1 -o out'
	print 'Run command:',com
	#Run NIST ROVER:
	returncode = os.system(com+'>/dev/null')
	if returncode != 0:
		print 'ROVER returncode error=',returncode
		sys.exit()
	#Read voting results from file "out"
	fid=open('out','rU')
	fusion = ''
	firstword=True
	for outline in fid.readlines():
		if firstword:	#Don't prepend a space for the first word
			fusion += outline.split()[4]	#Extract 5th column
			firstword=False
		else:
			fusion += ' ' + outline.split()[4]	#Extract 5th column
	fid.close()
	os.chdir(returnpath)	#Go back to the previous folder
	return fusion	#This is the improved (hopefully) hypothesis

def fake_data(orig,N=30,P=5):
	'''Create N corrupted versions of the test phrase, orig.
		P is the number of errors we put into the phrase.
	'''
	asrtext=[]	#Initialize a list of N corrupted transcripts
	for asr in range(N):	#For each corrupted transcript
		hyp=orig[0].split()	#Convert phrase to a list of words
		lh = len(hyp)		#Number of words
		#Corrupt each phrase with P random errors:
		for ii in range(P):
			idx=int(random.random()*lh)	#Pick a word at random
			rr=int(random.uniform(0,3))	#One of 3 error types
			if(rr==3): rr=2	#Very rare
			if rr==0:	#Insert word at location idx
				hyp.insert(idx,int(random.random()*1000))
				lh += 1
			if rr==1:	#Delete word at location idx
				if lh <= 0: continue
				del hyp[idx]
				lh -= 1
			if rr==2:	#Substitute word at idx
				if lh <= 0: continue
				hyp[idx] = -int(random.random()*1000)
		#Convert list into a string and append to asrtext[]
		textstring=' '.join(str(hh) for hh in hyp)
		asrtext.extend([textstring])
	return asrtext	#Return a list of corrupted hypotheses

def convert_data(orig):
	'''Convert transcriptions from CHiME to rover input format
	'''	
	asrtext=[]	#Initialize a list of N corrupted transcripts

if __name__ == "__main__": #Execute only if run as a script
	#Check command line format:
	if len(sys.argv) < 2:
		print 'Usage: '+sys.argv[0]+' original'
		sys.exit()
	#Read in a test phrase as the first line of the 'orig' file:
	orig=sys.argv[1]
	f=open(orig,'rU')
	orig = f.readlines()
	f.close()
	#Optionally initialize random number for repeatable tests
	if len(sys.argv) == 3:
		random.seed(int(sys.argv[2]))
	#Generate fake data with N=10 hypotheses and P=5 errors per hypothesis:
	asrtext=fake_data(orig,10,5)
	#Run rover
	fusion = runrover(asrtext,SCRATCH)
	print 'fusion=',fusion
	asrscores=[]
	for ii in asrtext:
		sclite_result = runsclite(orig,[ii])
		asrscores.extend([sclite_result])
		print 'ASR sclite_result:',sclite_result
		#raw_input(ii+' (Enter):')
	sclite_result = runsclite(orig,[fusion])
	print 'asrscores=',asrscores
	print 'FINAL: Average ASR_result=',1.0*sum(asrscores)/len(asrscores)
	print 'FINAL: Fusion sclite_result=',sclite_result
	#Run with: while true; do ./rover.py orig; done | grep KEEP



