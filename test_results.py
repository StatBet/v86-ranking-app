from scripts.result_parser import parse_results


sample = """
1
2 Chribo Hill
Conrad Lugauer
31

2
3 Mix the Booze
Björn Goop
717

3
6 Orosei Boko
Björn Goop
7603
"""


results = parse_results(sample)

print(results)