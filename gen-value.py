#!/usr/bin/env python

import yaml

def accounts_backend():
	with open('config.yaml', 'r') as g:
		docs = yaml.load_all(g, Loader=yaml.FullLoader)
		for doc in docs:
			for k, v in doc.items():
				for i, j in v.items():
					db = j[0]['type']
					with open('variables.yaml', 'r') as f:
						docs1 = yaml.load_all(f, Loader=yaml.FullLoader)
						for docu in docs1:
							for m, n in docu.items():
								if m==db:
									print(m, "->", n)
									fileNN1={}
									fileNN1[m]=n
	print(fileNN1)
	return fileNN1

if __name__=='__main__':
	accounts_backend()
