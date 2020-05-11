"""
Hook for https://pypi.org/project/SoundCard/
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('soundcard')
