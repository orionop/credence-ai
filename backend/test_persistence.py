import os
import json
from services.session import create_session, get_session, update_session, list_sessions

def test():
    print("Testing Persistence...")
    # 1. Create
    s = create_session(entity_name="Test Corp", sector="Tech")
    sid = s.id
    print(f"Created session: {sid}")
    
    # 2. Update
    update_session(sid, cin_gstin="12345", financials={"revenue": 1000})
    
    # 3. Retrieve
    s_retrieved = get_session(sid)
    print(f"Retrieved: {s_retrieved.entity_name}, Financials: {s_retrieved.financials}")
    
    # 4. Persistence check (re-import/re-init simulation happens via list_sessions)
    all_sessions = list_sessions()
    print(f"Total sessions in DB: {len(all_sessions)}")
    
    assert s_retrieved.entity_name == "Test Corp"
    assert s_retrieved.financials["revenue"] == 1000
    print("Persistence Test PASSED")

if __name__ == "__main__":
    test()
