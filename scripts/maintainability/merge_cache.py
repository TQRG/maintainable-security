import argparse
from os import listdir
from os.path import isfile, join
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from maintainability.cache import Cache

def change_extension(file_path, extension):
    return Path(file_path).stem + extension


def merge_cache(cache, output):
    cache_files = [f for f in listdir(cache) if isfile(join(cache, f)) and 'cache' in f]
    caches = [Cache(join(cache, f)) for f in cache_files]    
    merged_cache = caches[0]
    for cache in caches[1::]:
        merged_cache = merged_cache.merge_cache(cache)

    merged_cache.set_storage_path(output)
    merged_cache.save_data()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Report results')    
                        
    parser.add_argument('-cache', type=str, metavar='cache folder', help='cache folder path')  
    parser.add_argument('-output', type=str, metavar='output path', help='output folder path')      

    args = parser.parse_args()

    if args.cache != None and args.output != None:
         merge_cache(cache=args.cache, output=args.output)
    else:
        print('Something is wrong. Verify your parameters')
