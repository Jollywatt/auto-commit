"""
This file contains logic related to
- deciding whether to start a new commit
- describing commits
"""

class ActionDecider:
	def __init__(self):
		pass

	def should_be_new_change(self, report):
		"""
		Decide whether now is a good time to commit and start a new change.
		"""

		if report['n_files_affected'] == 0: return False # no changs

		return True