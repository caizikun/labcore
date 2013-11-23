# -*- coding: utf-8 -*-
from string import Formatter

from django.db import models
#from django.contrib.contenttypes.models import ContentType
#from django.contrib.contenttypes import generic
#from django.db.models import signals

from zutils.utils import make_signature


import utils
import device_comm

# Create your models here.


COMMAND_TYPES = (
    ('W', "Write"),
    ('A', "Ask"),
    ('B', "Ask Raw"),
                 
)


@utils.autoconnect
class BaseInstrument(models.Model):
    name = models.CharField(max_length = 256)
    base_instrument = models.ForeignKey('self', null = True)
    
    def add_command(self, command):
        if not command.pk:
            command.save()
        self.commands.add(command)
        self.make_command_function(command)
        if self.base_instrument:
            self.base_instrument.add_command()
        
    
    def create_command(self, *args, **kwargs):
        c = Command(*args, **kwargs)        
        self.add_command(c)
    
    def __unicode__(self):
        return self.name


class Instrument(BaseInstrument):

    
    device_id = models.CharField(max_length = 256, null = True)
    
    #interface = models.ForeignKey(Interface)
    #commands = models.ManyToManyField(Command)
    
    def make_command_function(self, command):
        attrname = utils.normalize_name(command.name)
        #if not hasattr(self, attrname):
        commandcall = command.make_callable(self)            
        setattr(self, attrname, commandcall)
        #else:
        #    raise ValueError("Name %s is already an instrument attribute")

    


    def make_interface(self):
        allcommands = self.commands.all()
        for command in allcommands:
            self.make_command_function(command)
        
    
        
    def post_init(self):
        #Execute if we have loaded the device and is already in the db
        if self.load_instrument() and self.pk:
             self.make_interface()
    
    def associate(self, device):
        self.device = device
        self.make_interface()

    def load_instrument(self):
        allins = device_comm.find_all()
        if self.device_id in allins:
            self.device = allins[self.device_id]
            return True
        else:
            return False


@utils.autoconnect
class BaseCommand(models.Model):
    name = models.CharField(max_length = 128)
    command_string = models.CharField(max_length = 1024)
    
    command_type = models.CharField(max_length = 1, choices = COMMAND_TYPES, 
                                    blank = True)
                                
    base_instrument = models.ForeignKey(BaseInstrument)

@utils.autoconnect
class Command(BaseCommand):
    
                                    
                                    
    #instrument can be I                                
    instrument = models.ForeignKey()
    
    
        
    description = models.TextField(default = "", blank = True)
    
    class ParamFinder(object):
        def __init__(self, command):
            self.command = command
        def __getitem__(self, key):
            return self.command.parameter_set.get(name = key)
            
    @property
    def parameters(self):
        return Command.ParamFinder(self)
    
    
    def save_params(self):
        f = Formatter()
        tokens = f.parse(self.command_string)
        
        param_names = []
        for (_ , param_name, _ , _) in tokens:
            if param_name is not None:
                self.parameter_set.get_or_create(name = param_name)
                param_names += [param_name]
            
                
        self.parameter_set.exclude(name__in = param_names).delete()
                
    def make_callable(self, instrument):
        
        params = self.parameter_set.all()
        argnames = []
        allnames = []
        kwargdefaults = {}
        for param in params:
            if param.default_value:
                kwargdefaults[param.name] = param.default_value
            else:
                argnames += [param.name]
            allnames += [param.name]
                
        ct = self.command_type
        if ct == "W":
            instrf = instrument.device.write
        elif ct == "A":
            instrf = instrument.device.ask
        elif ct == "B":
            instrf = instrument.device.ask_raw
        
        #f_factory is needed so that variables get bundled in f.
        def f_factory(command_string, loc_instrf, loc_argnames):

            def f(*args, **kwargs):
    
                argdict = {argname: arg 
                    for argname, arg in zip(loc_argnames, args)}
                        

                
                argdict.update(kwargs)

                instruction = command_string.format(**argdict)
                
                retval = loc_instrf(instruction)
                
                return retval
            
            return f
            
        s = self.command_string
       
        f = f_factory(s, instrf, argnames)        
                
        f.__doc__ = "%s\nThe query for this command is:\n%s"%(self.description,
                                self.command_string)
                                
        print ("Making callable for %s" % self.command_string)
        return make_signature(f, argnames, kwargdefaults)
        
        
    def pre_save(self):
        if not self.command_type:
            if self.command_string.endswith('?'):
                self.command_type = "A"
            else:
                self.command_type = "W"
    
    def post_save(self):
        self.save_params()
    


    def __unicode__(self):
        return self.name
        
class Parameter(models.Model):
    command = models.ForeignKey(Command, null = False)
    name = models.CharField(max_length = 128)
    default_value = models.CharField(max_length = 128, blank = True)
    description = models.TextField(default = "", blank = True)
    
    
    def __unicode__(self):
        return self.name


            
        
         
        
    
    