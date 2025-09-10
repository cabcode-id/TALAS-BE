import os
import importlib
from typing import List, Dict, Any, Optional


def get_crawler_modules():
    crawler_modules = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            crawler_modules.append(filename[:-3])
    
    return crawler_modules


def run_all_crawlers(**kwargs) -> List[Dict[str, Any]]:
    all_results = []
    crawler_modules = get_crawler_modules()
    
    # Check ada parameter pantai atau tidak 
    pantai_only = kwargs.pop('pantai', False)
    
    for module_name in crawler_modules:
        # Kalau pantai_only True, hanya jalankan module antarapantai
        if pantai_only and 'pantai' not in module_name:
            continue
        # Kalau pantai_only False, hanya jalankan module selain antarapantai
        if not pantai_only and 'pantai' in module_name:
            continue
            
        try:
            # Dynamically import the crawler module
            module_path = f"app.services.crawlers.{module_name}"
            module = importlib.import_module(module_path)
            
            # Check if the module has a main function
            if hasattr(module, 'main'):
                print(f"Running crawler: {module_name}")
                results = module.main(**kwargs)
                if results:
                    if isinstance(results, list):
                        all_results.extend(results)
                    else:
                        all_results.append(results)
                    print(f"Retrieved {len(results if isinstance(results, list) else [results])} results from {module_name}")
                else:
                    print(f"No results from {module_name}")
            else:
                print(f"Warning: {module_name} does not have a main function")
        except Exception as e:
            print(f"Error running {module_name}: {str(e)}")
    
    return all_results


def main(**kwargs) -> List[Dict[str, Any]]:
    return run_all_crawlers(**kwargs)


if __name__ == "__main__":
    results = main()
    print(f"Total results from all crawlers: {len(results)}")