#!/usr/bin/env python3
"""
Quick test script for the dynamic tier system
"""

from skill_intelligence_engine import analyze_all_skills_with_advanced_intelligence

if __name__ == "__main__":
    print("🧪 TESTING DYNAMIC TIER SYSTEM")
    print("="*50)
    print("Running comprehensive analysis with dynamic tiers and decoder ring...")
    
    # Run the analysis
    results = analyze_all_skills_with_advanced_intelligence("test_dynamic_tiers_output.csv")
    
    if len(results) > 0:
        print(f"\n✅ SUCCESS! Generated {len(results):,} skills with dynamic tiers")
        
        # Show tier distribution
        tier_counts = results['intelligence_tier'].value_counts()
        print(f"\n🏆 Final Tier Distribution:")
        for tier, count in tier_counts.items():
            print(f"   → {tier}: {count}")
        
        # Check for any "Unknown" tiers
        unknown_count = tier_counts.get("Unknown", 0)
        if unknown_count == 0:
            print(f"\n🎉 PERFECT! No 'Unknown' tiers - dynamic system working!")
        else:
            print(f"\n⚠️ Still have {unknown_count} 'Unknown' tiers")
            
    else:
        print("❌ FAILED - No results generated") 