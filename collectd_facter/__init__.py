#===============================================================================
# collectd-facter - a generic plugin for gathering numeric Facter facts
#
#  SOURCE
#        https://github.com/ghetzel/collectd-facter
#
#  AUTHOR
#        Gary Hetzel <garyhetzel@gmail.com>
#===============================================================================
import collectd
import json
import sys
import os
import subprocess

# -----------------------------------------------------------------------------
# CALLBACK: config()
#   processes the collectd.conf configuration stanza for this plugin
#
def config(c):
  global facts, config

  facts = {}

  for ci in c.children:
    if ci.key == 'FactFile':
      try:
        f = open(os.path.abspath(ci.values[0]), 'r')

        for fact in f:
          if len(fact.strip()) > 0:
            fact = fact.split(':')
            if len(fact) > 1:
              value = fact[1]
            else:
              value = fact[0]

            facts[fact[0]] = value

        f.close()

      except IOError, e:
        raise Exception('Error opening FactFile %s: %s' % (ci.values[0], e))

    elif ci.key == 'Fact':
      fact = ci.values[0]

      if len(ci.values) > 1:
        value = ci.values[1]
      else:
        value = ci.values[0]

      facts[fact] = value



# -----------------------------------------------------------------------------
# CALLBACK: collectd write()
#   this is what collectd calls when it receives a new metric observation
#
def read(data=None):
  global facts

  env = os.environ.copy()
  env['FACTERLIB'] = '/etc/facter'

  output = subprocess.Popen((['facter', '--json']+facts.keys()), 
stdout=subprocess.PIPE, env=env)
  output.wait()
  output = output.stdout.read()

  vl = collectd.Values(type='gauge')
  vl.plugin = 'facter'

  try:
    values = json.loads(output)

    for fact in facts.keys():
      if fact:
        if fact in values:
          try:
            value = float(values[fact])
            vl.plugin_instance = facts[fact]
            vl.dispatch(values=[value])
          except Exception, e:
            pass

  except Exception, e:
    pass

# -----------------------------------------------------------------------------
# shutdown
#   called once on daemon shutdown
#
def shutdown():
  print "Stopping collectd-facter"


# -----------------------------------------------------------------------------
# Register Callbacks
# -----------------------------------------------------------------------------
collectd.register_config(config)
collectd.register_read(read)
collectd.register_shutdown(shutdown)

