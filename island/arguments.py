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
from . import debug

##
## @brief Single argument class. It permit to define the getted argument.
##
class ArgElement:
	##
	## @brief Contructor.
	## @param[in] self Class handle
	## @param[in] option (string) Option name (write in fullmode ex: '--verbose' even if user write '-v')
	## @param[in] value (string) Writed value by the user (defult '')
	##
	def __init__(self, option, value=""):
		self.option = option;
		self.arg = value;
	
	##
	## @brief Get the name of the argument: (write in fullmode ex: '--verbose' even if user write '-v')
	## @param[in] self Class handle
	## @return (string) The argument name
	##
	def get_option_name(self):
		return self.option
	
	##
	## @brief Get argument data set by the user
	## @param[in] self Class handle
	## @return (string) The argument value
	##
	def get_arg(self):
		return self.arg
	
	##
	## @brief Display the Argument property
	## @param[in] self Class handle
	##
	def display(self):
		if len(self.arg) == 0:
			debug.info("option : " + self.option)
		elif len(self.option) == 0:
			debug.info("element :       " + self.arg)
		else:
			debug.info("option : " + self.option + ":" + self.arg)

##
## @brief Declare a possibility of an argument value
##
class ArgDefine:
	##
	## @brief Contructor.
	## @param[in] self Class handle
	## @param[in] smallOption (char) Value for the small option ex: '-v' '-k' ... 1 single char element (no need of '-')
	## @param[in] bigOption (string) Value of the big option name ex: '--verbose' '--kill' ... stated with -- and with the full name (no need of '--')
	## @param[in] list ([[string,string],...]) Optionnal list of availlable option: '--mode=debug' ==> [['debug', 'debug mode'],['release', 'release the software']]
	## @param[in] desc (string) user friendly description with this parameter (default "")
	## @param[in] haveParam (bool) The option must have a parameter (default False)
	##
	def __init__(self,
	             smallOption="", # like v for -v
	             bigOption="", # like verbose for --verbose
	             list=[], # ["val", "description"]
	             desc="",
	             haveParam=False):
		self.option_small = smallOption;
		self.option_big = bigOption;
		self.list = list;
		if len(self.list)!=0:
			self.have_param = True
		else:
			if True==haveParam:
				self.have_param = True
			else:
				self.have_param = False
		self.description = desc;
	
	def is_parsable(self):
		return True
	##
	## @brief Get the small name of the option ex: '-v'
	## @param[in] self Class handle
	## @return (string) Small name value
	##
	def get_option_small(self):
		return self.option_small
	
	##
	## @brief Get the big name of the option ex: '--verbose'
	## @param[in] self Class handle
	## @return (string) Big name value
	##
	def get_option_big(self):
		return self.option_big
	
	##
	## @brief Get the status of getting user parameter value
	## @param[in] self Class handle
	## @return True The user must write a value
	## @return False The user must NOT write a value
	##
	def need_parameters(self):
		return self.have_param
	
	##
	## @brief Compatibility with @ref ArgSection class
	## @param[in] self Class handle
	## @return (string) empty string
	##
	def get_porperties(self):
		return ""
	
	##
	## @brief Check if the user added value is correct or not with the list of availlable value
	## @param[in] self Class handle
	## @param[in] argument (string) User parameter value (string)
	## @return True The parameter is OK
	## @return False The parameter is NOT Availlable
	##
	def check_availlable(self, argument):
		if len(self.list)==0:
			return True
		for element,desc in self.list:
			if element == argument:
				return True
		return False
	
	##
	## @brief Display the argument property when user request help
	## @param[in] self Class handle
	##
	def display(self):
		color = debug.get_color_set()
		if self.option_small != "" and self.option_big != "":
			print("		" + color['red'] + "-" + self.option_small + "" + color['default'] + " / " + color['red'] + "--" + self.option_big + color['default'])
		elif self.option_small != "":
			print("		" + color['red'] + "-" + self.option_small + color['default'])
		elif self.option_big != "":
			print("		" + color['red'] + "--" + self.option_big + color['default'])
		else:
			print("		???? ==> internal error ...")
		if self.description != "":
			print("			" + self.description)
		if len(self.list)!=0:
			hasDescriptiveElement=False
			for val,desc in self.list:
				if desc!="":
					hasDescriptiveElement=True
					break;
			if hasDescriptiveElement==True:
				for val,desc in self.list:
					print("				" + val + " : " + desc)
			else:
				tmpElementPrint = ""
				for val,desc in self.list:
					if len(tmpElementPrint)!=0:
						tmpElementPrint += " / "
					tmpElementPrint += val
				print("				{ " + tmpElementPrint + " }")


##
## @brief Declare an argument value and store it in a parameter
##
class ArgVolatile:
	##
	## @brief Contructor.
	## @param[in] self Class handle
	## @param[in] dest_option (string) Where to store the option name
	## @param[in] optionnal (bool) this element can be not present
	## @param[in] desc (string) user friendly description with this parameter (default "")
	##
	def __init__(self,
	             dest_option="",
	             optionnal=False,
	             desc=""):
		self.dest_option = dest_option;
		if dest_option == "":
			debug.error("volatil argument must be store in an argument name")
		self.optionnal = optionnal;
		self.description = desc;
		self.count = 0;
	
	def is_parsable(self):
		return False
	##
	## @brief Get the small name of the option ex: '-v'
	## @param[in] self Class handle
	## @return (string) Small name value
	##
	def get_option_small(self):
		return ""
	
	##
	## @brief Get the big name of the option ex: '--verbose'
	## @param[in] self Class handle
	## @return (string) Big name value
	##
	def get_option_big(self):
		return self.dest_option
	
	##
	## @brief Get the status of getting user parameter value
	## @param[in] self Class handle
	## @return True The user must write a value
	## @return False The user must NOT write a value
	##
	def need_parameters(self):
		if self.count == 0:
			self.count += 1
			return True
		return False
	
	##
	## @brief Compatibility with @ref ArgSection class
	## @param[in] self Class handle
	## @return (string) empty string
	##
	def get_porperties(self):
		return " [" + self.dest_option + "]"
	
	##
	## @brief Check if the user added value is correct or not with the list of availlable value
	## @param[in] self Class handle
	## @param[in] argument (string) User parameter value (string)
	## @return True The parameter is OK
	## @return False The parameter is NOT Availlable
	##
	def check_availlable(self, argument):
		return True
	
	##
	## @brief Display the argument property when user request help
	## @param[in] self Class handle
	##
	def display(self):
		color = debug.get_color_set()
		print("		" + color['red'] + "[" + self.dest_option + "]" + color['default'])
		if self.optionnal == True:
			print("(OPTIONNAL)")
		if self.description != "":
			print("			" + self.description)

##
## @brief Section Class definition (permit to add a comment when requesting help
##
class ArgSection:
	##
	## @brief Constructor
	## @param[in] self Class handle
	## @param[in] sectionName (string) Name of the cestion ex: "option" is displayed [option]
	## @param[in] desc (string) Comment assiciated with the group
	##
	def __init__(self,
	             sectionName="",
	             desc=""):
		self.section = sectionName;
		self.description = desc;
	
	def is_parsable(self):
		return False
	
	##
	## @brief Compatibility with @ref ArgDefine class
	## @param[in] self Class handle
	## @return empty string
	##
	def get_option_small(self):
		return ""
	
	##
	## @brief Compatibility with @ref ArgDefine class
	## @param[in] self Class handle
	## @return empty string
	##
	def get_option_big(self):
		return ""
	
	##
	## @brief get property print value with the correct writing mode
	## @param[in] self Class handle
	## @return String to display in the short line help
	##
	def get_porperties(self):
		color = debug.get_color_set()
		return " [" + color['blue'] + self.section + color['default'] + "]"
	
	##
	## @brief Display the argument property when user request help
	## @param[in] self Class handle
	##
	def display(self):
		color = debug.get_color_set()
		print("	[" + color['blue'] + self.section + color['default'] + "] : " + self.description)





##
## @brief Class to define the agmument list availlable for a program
##
class islandArg:
	##
	## @brief Constructor.
	## @param[in] self Class handle
	##
	def __init__(self):
		self.list_properties = []
		self._list_element_stop = []
		self._last_element_parsed = 0
	
	##
	## @brief Add a new argument possibilities...
	## @param[in] self Class handle
	## @param[in] smallOption (char) Value for the small option ex: '-v' '-k' ... 1 single char element (no need of '-')
	## @param[in] bigOption (string) Value of the big option name ex: '--verbose' '--kill' ... stated with -- and with the full name (no need of '--')
	## @param[in] list ([[string,string],...]) Optionnal list of availlable option: '--mode=debug' ==> [['debug', 'debug mode'],['release', 'release the software']]
	## @param[in] desc (string) user friendly description with this parameter (default "")
	## @param[in] haveParam (bool) The option must have a parameter (default False)
	##
	def add(self, smallOption="", bigOption="", list=[], desc="", haveParam=False):
		self.list_properties.append(ArgDefine(smallOption, bigOption, list, desc, haveParam))
	
	def add_arg(self, destOption="", optionnal=False, desc=""):
		self.list_properties.append(ArgVolatile(destOption, optionnal, desc))
	
	##
	## @brief Add section on argument list
	## @param[in] self Class handle
	## @param[in] sectionName (string) Name of the cestion ex: "option" is displayed [option]
	## @param[in] sectionDesc (string) Comment assiciated with the group
	##
	def add_section(self, sectionName, sectionDesc):
		self.list_properties.append(ArgSection(sectionName, sectionDesc))
	
	##
	## @brief Parse the argument set in the command line
	## @param[in] self Class handle
	## @param[in] start_position_parsing position to start the parsing in the arguments
	##
	def parse(self, start_position_parsing=1):
		list_argument = [] # composed of list element
		not_parse_next_element=False
		for iii in range(start_position_parsing, len(sys.argv)):
			self._last_element_parsed = iii
			# special case of parameter in some elements
			if not_parse_next_element == True:
				not_parse_next_element = False
				continue
			debug.verbose("parse [" + str(iii) + "]=" + sys.argv[iii])
			argument = sys.argv[iii]
			# check if we get a stop parsing element:
			if argument in self._list_element_stop:
				debug.warning("stop at position: " + str(iii))
				list_argument.append(ArgElement("", argument))
				break;
			optionList = argument.split("=")
			debug.verbose(str(optionList))
			if type(optionList) == type(str()):
				option = optionList
			else:
				option = optionList[0]
			optionParam = argument[len(option)+1:]
			debug.verbose(option)
			argument_found=False;
			if option[:2] == "--":
				# big argument
				for prop in self.list_properties:
					if prop.is_parsable()==False:
						continue
					if prop.get_option_big()=="":
						continue
					if prop.get_option_big() == option[2:]:
						# find it
						debug.verbose("find argument 2 : " + option[2:])
						if prop.need_parameters()==True:
							internalSub = option[2+len(prop.get_option_big()):]
							if len(internalSub)!=0:
								if len(optionParam)!=0:
									# wrong argument ...
									debug.warning("maybe wrong argument for : '" + prop.get_option_big() + "' cmdLine='" + argument + "'")
									prop.display()
									continue
								optionParam = internalSub
							if len(optionParam)==0:
								#Get the next parameters 
								if len(sys.argv) > iii+1:
									optionParam = sys.argv[iii+1]
									not_parse_next_element=True
								else :
									# missing arguments
									debug.warning("parsing argument error : '" + prop.get_option_big() + "' Missing : subParameters ... cmdLine='" + argument + "'")
									prop.display()
									exit(-1)
							if prop.check_availlable(optionParam)==False:
								debug.warning("argument error : '" + prop.get_option_big() + "' SubParameters not availlable ... cmdLine='" + argument + "' option='" + optionParam + "'")
								prop.display()
								exit(-1)
							list_argument.append(ArgElement(prop.get_option_big(),optionParam))
							argument_found = True
						else:
							if len(optionParam)!=0:
								debug.warning("parsing argument error : '" + prop.get_option_big() + "' need no subParameters : '" + optionParam + "'   cmdLine='" + argument + "'")
								prop.display()
							list_argument.append(ArgElement(prop.get_option_big()))
							argument_found = True
						break;
				if argument_found == False:
					debug.error("UNKNOW argument : '" + argument + "'")
			elif option[:1]=="-":
				# small argument
				for prop in self.list_properties:
					if prop.is_parsable()==False:
						continue
					if prop.get_option_small()=="":
						continue
					if prop.get_option_small() == option[1:1+len(prop.get_option_small())]:
						# find it
						debug.verbose("find argument 1 : " + option[1:1+len(prop.get_option_small())])
						if prop.need_parameters()==True:
							internalSub = option[1+len(prop.get_option_small()):]
							if len(internalSub)!=0:
								if len(optionParam)!=0:
									# wrong argument ...
									debug.warning("maybe wrong argument for : '" + prop.get_option_big() + "' cmdLine='" + argument + "'")
									prop.display()
									continue
								optionParam = internalSub
							if len(optionParam)==0:
								#Get the next parameters 
								if len(sys.argv) > iii+1:
									optionParam = sys.argv[iii+1]
									not_parse_next_element=True
								else :
									# missing arguments
									debug.warning("parsing argument error : '" + prop.get_option_big() + "' Missing : subParameters  cmdLine='" + argument + "'")
									prop.display()
									exit(-1)
							if prop.check_availlable(optionParam)==False:
								debug.warning("argument error : '" + prop.get_option_big() + "' SubParameters not availlable ... cmdLine='" + argument + "' option='" + optionParam + "'")
								prop.display()
								exit(-1)
							list_argument.append(ArgElement(prop.get_option_big(),optionParam))
							argument_found = True
						else:
							if len(optionParam)!=0:
								debug.warning("parsing argument error : '" + prop.get_option_big() + "' need no subParameters : '" + optionParam + "'  cmdLine='" + argument + "'")
								prop.display()
							list_argument.append(ArgElement(prop.get_option_big()))
							argument_found = True
						break;
			
			if argument_found==False:
				# small argument
				for prop in self.list_properties:
					if    prop.is_parsable() == True \
					   or prop.get_option_big() == "":
						continue
					if prop.need_parameters() == True:
						list_argument.append(ArgElement(prop.get_option_big(), argument))
						argument_found = True
						break
			if argument_found==False:
				#unknow element ... ==> just add in the list ...
				debug.verbose("unknow argument : " + argument)
				list_argument.append(ArgElement("", argument))
			
		for prop in self.list_properties:
			if    prop.is_parsable() == True \
			   or prop.get_option_big() == "":
				continue
			if     prop.need_parameters() == True \
			   and prop.optionnal == False:
				debug.error("Missing argument:" + prop.get_option_big())
		#for argument in list_argument:
		#	argument.display()
		#exit(0)
		return list_argument;
	
	##
	## @brief Stop parsing at a specific position
	## @param[in] self Class handle
	## @param[in] list_of_element List of element that stop the parsing
	##
	def set_stop_at(self, list_of_element):
		self._list_element_stop = list_of_element
	
	##
	## @brief get the last element parsed.
	## @param[in] self Class handle
	##
	def get_last_parsed(self):
		return self._last_element_parsed
	
	##
	## @brief Display help on console output
	## @param[in] self Class handle
	## @param[in] action_name opation to set at the end of the application name
	##
	def display(self, action_name=""):
		print("usage:")
		listOfPropertiesArg = "";
		for element in self.list_properties :
			listOfPropertiesArg += element.get_porperties()
		print("	" + sys.argv[0] + " " + action_name + " " + listOfPropertiesArg + " ...")
		for element in self.list_properties :
			element.display()

