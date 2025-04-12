"""Wallet listening module

This wallet listening module is mainly used to monitor its own wallet changes, including:
- sol balance change
- token balance changes
- Build a position (i.e., create a new ata)
- Clearance (i.e. delete ata)
- Increase position (in the presence of ata, add token)
- Reduce positions (in the presence of ata, reduce tokens)
"""