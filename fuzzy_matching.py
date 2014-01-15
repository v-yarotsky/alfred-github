import re
import string

def fuzzy_match(input_str, target_str):
  return __normalize__(target_str).find(__normalize__(input_str)) != -1

def __normalize__(s):
  # change punctuation to underscores
  for p in string.punctuation:
      s = s.replace(p, '_')
  # change camelCase to underscores
  s = re.sub('([a-z0-9])([A-Z])', '\\1_\\2', s)
  return s.lower().strip()

