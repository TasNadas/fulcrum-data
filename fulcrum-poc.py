import fulcrum, sys, json, os, codecs, string, math
from fulcrum import Fulcrum

api_key = os.environ['FULCRUM_API_KEY']

fulcrum = Fulcrum(key=api_key)

proj = {}

proj['name'] = 'My New Project'

wrapper = {}

wrapper['project'] = proj

print fulcrum.projects.find('86d4b7cd-4e8d-4260-b69c-747301c06835')


# class Project:
#     def __init__(self, name=None, description=None):
#         self.name = name
#         self.description = description
#
#     def __str__(self):
#         return self.name + ' is the best project'
#
# a_proj = Project('My New Project')
#
# print wrapper
# print a_proj