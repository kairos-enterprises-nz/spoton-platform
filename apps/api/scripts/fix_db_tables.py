#!/usr/bin/env python3

# Read the models file and fix the db_table settings
with open('Spoton_Backend/users/models.py', 'r') as f:
    content = f.read()

# Fix the db_table settings - remove the extra quotes
replacements = [
    ('db_table = \'users."users.users_tenant"\'', 'db_table = \'users."users.users_tenant"\''),
    ('db_table = \'users."users.users_user"\'', 'db_table = \'users."users.users_user"\''),
    ('db_table = \'users."users.users_otp"\'', 'db_table = \'users."users.users_otp"\''),
    ('db_table = \'users."users.users_userchangelog"\'', 'db_table = \'users."users.users_userchangelog"\''),
    ('db_table = \'users."users.users_account"\'', 'db_table = \'users."users.users_account"\''),
    ('db_table = \'users."users.users_useraccountrole"\'', 'db_table = \'users."users.users_useraccountrole"\''),
]

for old, new in replacements:
    content = content.replace(old, new)
    print(f"Replaced: {old} -> {new}")

# Write the fixed content back
with open('Spoton_Backend/users/models.py', 'w') as f:
    f.write(content)

print("Fixed all db_table settings!") 