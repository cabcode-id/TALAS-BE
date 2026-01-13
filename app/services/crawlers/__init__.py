import os
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional


def get_crawler_modules():
    crawler_modules = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            crawler_modules.append(filename[:-3])
    
    return crawler_modules


def _filter_crawler_modules(crawler_modules: List[str], pantai_only: bool) -> List[str]:
    filtered_modules = []
    for module_name in crawler_modules:
        if pantai_only and 'pantai' not in module_name:
            continue
        if not pantai_only and 'pantai' in module_name:
            continue
        filtered_modules.append(module_name)
    return filtered_modules


def run_all_crawlers(**kwargs) -> List[Dict[str, Any]]:
    all_results = []
    crawler_modules = get_crawler_modules()
    
    # Check ada parameter pantai atau tidak 
    pantai_only = kwargs.pop('pantai', False)

    crawler_modules = _filter_crawler_modules(crawler_modules, pantai_only)

    for module_name in crawler_modules:
            
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


def run_all_crawlers_parallel(**kwargs) -> List[Dict[str, Any]]:
    all_results = []
    crawler_modules = get_crawler_modules()

    # Check ada parameter pantai atau tidak 
    pantai_only = kwargs.pop('pantai', False)
    crawler_modules = _filter_crawler_modules(crawler_modules, pantai_only)

    if not crawler_modules:
        return all_results

    max_workers = min(8, len(crawler_modules))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for module_name in crawler_modules:
            try:
                module_path = f"app.services.crawlers.{module_name}"
                module = importlib.import_module(module_path)
                if not hasattr(module, 'main'):
                    print(f"Warning: {module_name} does not have a main function")
                    continue
                print(f"Running crawler: {module_name}")
                params = dict(kwargs)
                futures[executor.submit(module.main, **params)] = module_name
            except Exception as e:
                print(f"Error running {module_name}: {str(e)}")

        for future in as_completed(futures):
            module_name = futures[future]
            try:
                results = future.result()
                if results:
                    if isinstance(results, list):
                        all_results.extend(results)
                        count = len(results)
                    else:
                        all_results.append(results)
                        count = 1
                    print(f"Retrieved {count} results from {module_name}")
                else:
                    print(f"No results from {module_name}")
            except Exception as e:
                print(f"Error running {module_name}: {str(e)}")

    return all_results


def main(**kwargs) -> List[Dict[str, Any]]:
    parallel = kwargs.pop('parallel', False)
    if parallel:
        return run_all_crawlers_parallel(**kwargs)
    return run_all_crawlers(**kwargs)


if __name__ == "__main__":
    results = main()
    print(f"Total results from all crawlers: {len(results)}")
