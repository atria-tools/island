#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

import sys
import threading
import time
import sys
if sys.version_info >= (3, 0):
	import queue
else:
	import Queue as queue
import os
import subprocess
import shlex
# Local import
from . import debug
from . import tools
from . import env
from . import depend

queue_lock = threading.Lock()
work_queue = queue.Queue()
current_thread_working = 0
threads = []
# To know the first error arrive in the pool ==> to display all the time the same error file when multiple compilation
current_id_execution = 0
error_execution = {
	"id":-1,
	"cmd":"",
	"return":0,
	"err":"",
	"out":"",
}

exit_flag = False # resuest stop of the thread
is_init = False # the thread are initialized
error_occured = False # a thread have an error
processor_availlable = 1 # number of CPU core availlable
##
## @brief Execute the command with no get of output
##
def run_command_no_lock_out(cmd_line):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.info("cmd = " + str(args))
	try:
		# create the subprocess
		p = subprocess.Popen(args)
	except subprocess.CalledProcessError as e:
		debug.error("subprocess.CalledProcessError : " + str(args))
		return
	#except:
	#	debug.error("Exception on : " + str(args))
	# launch the subprocess:
	p.communicate()

##
## @brief Execute the command and ruturn generate data
##
def run_command_direct(cmd_line):
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	try:
		# create the subprocess
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as e:
		debug.error("subprocess.CalledProcessError : " + str(args))
	except:
		debug.error("Exception on : " + str(args))
	# launch the subprocess:
	output, err = p.communicate()
	if sys.version_info >= (3, 0):
		output = output.decode("utf-8")
		err = err.decode("utf-8")
	# Check error :
	if p.returncode == 0:
		if output == None:
			return err[:-1];
		return output[:-1];
	else:
		return False


def run_command(cmd_line, store_cmd_line="", build_id=-1, file="", store_output_file="", depend_data=None):
	global error_occured
	global exit_flag
	global current_id_execution
	global error_execution
	# prepare command line:
	args = shlex.split(cmd_line)
	debug.verbose("cmd = " + str(args))
	try:
		# create the subprocess
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as e:
		debug.error("subprocess.CalledProcessError : TODO ...")
	except:
		debug.error("Exception on : " + str(args))
	# launch the subprocess:
	output, err = p.communicate()
	if sys.version_info >= (3, 0):
		output = output.decode("utf-8")
		err = err.decode("utf-8")
	# store error if needed:
	tools.store_warning(store_output_file, output, err)
	# Check error :
	if p.returncode == 0:
		debug.debug(env.print_pretty(cmd_line))
		queue_lock.acquire()
		if depend_data != None:
			depend.create_dependency_file(depend_data['file'], depend_data['data'])
		# TODO : Print the output all the time .... ==> to show warnings ...
		if build_id >= 0 and (output != "" or err != ""):
			debug.warning("output in subprocess compiling: '" + file + "'")
		if output != "":
			debug.print_compilator(output)
		if err != "":
			debug.print_compilator(err)
		queue_lock.release()
	else:
		error_occured = True
		exit_flag = True
		# if No ID : Not in a multiprocess mode ==> just stop here
		if build_id < 0:
			debug.debug(env.print_pretty(cmd_line), force=True)
			debug.print_compilator(output)
			debug.print_compilator(err)
			if p.returncode == 2:
				debug.error("can not compile file ... [keyboard interrrupt]")
			else:
				debug.error("can not compile file ... ret : " + str(p.returncode))
		else:
			# in multiprocess interface
			queue_lock.acquire()
			# if an other write an error before, check if the current process is started before ==> then is the first error
			if error_execution["id"] >= build_id:
				# nothing to do ...
				queue_lock.release()
				return;
			error_execution["id"] = build_id
			error_execution["cmd"] = cmd_line
			error_execution["return"] = p.returncode
			error_execution["err"] = err,
			error_execution["out"] = output,
			queue_lock.release()
		# not write the command file...
		return
	debug.verbose("done 3")
	# write cmd line only after to prevent errors ...
	tools.store_command(cmd_line, store_cmd_line)



class myThread(threading.Thread):
	def __init__(self, thread_id, lock, queue):
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.name = "Thread " + str(thread_id)
		self.queue = queue
		self.lock = lock
	def run(self):
		debug.verbose("Starting " + self.name)
		global exit_flag
		global current_thread_working
		working_set = False
		while exit_flag == False:
			self.lock.acquire()
			if not self.queue.empty():
				if working_set == False:
					current_thread_working += 1
					working_set = True
				data = self.queue.get()
				self.lock.release()
				debug.verbose(self.name + " processing '" + data[0] + "'")
				if data[0]=="cmd_line":
					comment = data[2]
					cmd_line = data[1]
					cmd_store_file = data[3]
					debug.print_element("[" + str(data[4]) + "][" + str(self.thread_id) + "] " + comment[0],
					                    comment[1],
					                    comment[2],
					                    comment[3])
					run_command(cmd_line,
					            cmd_store_file,
					            build_id=data[4],
					            file=comment[3],
					            store_output_file=data[5],
					            depend_data=data[6])
				else:
					debug.warning("unknow request command : " + data[0])
			else:
				if working_set==True:
					current_thread_working -= 1
					working_set=False
				# no element to parse, just wait ...
				self.lock.release()
				time.sleep(0.2)
		# kill requested ...
		debug.verbose("Exiting " + self.name)


def set_error_occured():
	global exit_flag
	exit_flag = True

def set_core_number(number_of_core):
	global processor_availlable
	processor_availlable = number_of_core
	debug.debug(" set number of core for multi process compilation : " + str(processor_availlable))
	# nothing else to do

def init():
	global error_occured
	global exit_flag
	global is_init
	if is_init == False:
		is_init = True
		error_occured = False
		global threads
		global queue_lock
		global work_queue
		# Create all the new threads
		thread_id = 0
		while thread_id < processor_availlable:
			thread = myThread(thread_id, queue_lock, work_queue)
			thread.start()
			threads.append(thread)
			thread_id += 1
		


def un_init():
	global exit_flag
	# Notify threads it's time to exit
	exit_flag = True
	if processor_availlable > 1:
		# Wait for all threads to complete
		for tmp in threads:
			debug.verbose("join thread ...")
			tmp.join()
		debug.verbose("Exiting ALL Threads")



def run_in_pool(cmd_line, comment, store_cmd_line="", store_output_file="", depend_data=None):
	global current_id_execution
	if processor_availlable <= 1:
		debug.print_element(comment[0], comment[1], comment[2], comment[3])
		run_command(cmd_line, store_cmd_line, file=comment[3], store_output_file=store_output_file, depend_data=depend_data)
		return
	# multithreaded mode
	init()
	# Fill the queue
	queue_lock.acquire()
	debug.verbose("add : in pool cmd_line")
	work_queue.put(["cmd_line", cmd_line, comment, store_cmd_line, current_id_execution, store_output_file, depend_data])
	current_id_execution +=1;
	queue_lock.release()
	

def pool_synchrosize():
	global error_occured
	global error_execution
	if processor_availlable <= 1:
		#in this case : nothing to synchronise
		return
	
	debug.verbose("wait queue process ended\n")
	# Wait for queue to empty
	while not work_queue.empty() \
	      and error_occured == False:
		time.sleep(0.2)
		pass
	# Wait all thread have ended their current process
	while current_thread_working != 0 \
	      and error_occured == False:
		time.sleep(0.2)
		pass
	if error_occured == False:
		debug.verbose("queue is empty")
	else:
		un_init()
		debug.debug("Thread return with error ... ==> stop all the pool")
		if error_execution["id"] == -1:
			debug.error("Pool error occured ... (No return information on Pool)")
			return
		debug.error("Error in an pool element : [" + str(error_execution["id"]) + "]", crash=False)
		debug.debug(env.print_pretty(error_execution["cmd"]), force=True)
		debug.print_compilator(str(error_execution["out"][0]))
		debug.print_compilator(str(error_execution["err"][0]))
		if error_execution["return"] == 2:
			debug.error("can not compile file ... [keyboard interrrupt]")
		else:
			debug.error("can not compile file ... return value : " + str(error_execution["return"]))
	
