from Start import app

print("All registered routes:")
print("-" * 60)
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods))
    print(f"{rule.rule:50s} {methods:20s} {rule.endpoint}")