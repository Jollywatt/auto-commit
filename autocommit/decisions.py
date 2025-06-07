"""
This file contains logic related to
- deciding whether to start a new commit
- describing commits
"""

class ActionDecider:
	def __init__(self):
		pass

	def should_be_new_change(self, report):
		return True