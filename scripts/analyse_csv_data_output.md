PS C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine> python scripts/analyze_csv_data.py
🔍 CSV DATA ANALYSIS TOOL
============================================================
📂 Analyzing all CSV files in /data/ directory
🏠 Project Root: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine
📁 Data Directory: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data

🔍 Searching for CSV files...
📄 Found 19 CSV files

🔄 Analyzing 1/19: data\colleague_positions_history\d_colleague_position_fy22.csv
🔄 Analyzing 2/19: data\colleague_positions_history\d_colleague_position_fy23.csv
🔄 Analyzing 3/19: data\colleague_positions_history\d_colleague_position_fy24.csv
🔄 Analyzing 4/19: data\colleague_positions_history\d_colleague_position_fy25.csv
🔄 Analyzing 5/19: data\job_arch_to_positions_mapping\job_arch_to_positions_mapping.csv
🔄 Analyzing 6/19: data\job_architecture\job_architecture.csv
🔄 Analyzing 7/19: data\job_skill_mapping\job_skill_mapping.csv
🔄 Analyzing 8/19: data\positions_history\d_positions_fy21.csv
🔄 Analyzing 9/19: data\positions_history\d_positions_fy22.csv
🔄 Analyzing 10/19: data\positions_history\d_positions_fy23.csv
🔄 Analyzing 11/19: data\positions_history\d_positions_fy24.csv
🔄 Analyzing 12/19: data\positions_history\d_positions_fy25.csv
🔄 Analyzing 13/19: data\skills_library\meta.csv
🔄 Analyzing 14/19: data\skills_library\skills_9.32.csv
🔄 Analyzing 15/19: data\skills_library\skills_comprehensive_all_versions.csv
🔄 Analyzing 16/19: data\skills_library\status.csv
🔄 Analyzing 17/19: data\skills_library\version_latest.csv
🔄 Analyzing 18/19: data\skills_library\versions.csv
🔄 Analyzing 19/19: data\workforce_context\workforce_context.csv

================================================================================
CSV DATA ANALYSIS REPORT
================================================================================
Analysis Date: 2025-07-30 13:32:37
Data Directory: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data
Total CSV Files Found: 19

✅ Successfully Analyzed: 19
❌ Failed to Analyze: 0

📁 FILES BY DIRECTORY
--------------------------------------------------

📂 colleague_positions_history/
   Files: 4 | Total Size: 124.72 MB | Total Rows: 2,000,000
   └── d_colleague_position_fy22.csv (500,000 rows × 6 cols, 30.90 MB)
   └── d_colleague_position_fy23.csv (500,000 rows × 6 cols, 31.06 MB)
   └── d_colleague_position_fy24.csv (500,000 rows × 6 cols, 31.38 MB)
   └── d_colleague_position_fy25.csv (500,000 rows × 6 cols, 31.38 MB)

📂 job_arch_to_positions_mapping/
   Files: 1 | Total Size: 0.09 MB | Total Rows: 5,000
   └── job_arch_to_positions_mapping.csv (5,000 rows × 2 cols, 0.09 MB)

📂 job_architecture/
   Files: 1 | Total Size: 0.12 MB | Total Rows: 715
   └── job_architecture.csv (715 rows × 16 cols, 0.12 MB)

📂 job_skill_mapping/
   Files: 1 | Total Size: 1.15 MB | Total Rows: 40,170
   └── job_skill_mapping.csv (40,170 rows × 2 cols, 1.15 MB)

📂 positions_history/
   Files: 5 | Total Size: 46.79 MB | Total Rows: 600,000
   └── d_positions_fy21.csv (120,000 rows × 9 cols, 9.36 MB)
   └── d_positions_fy22.csv (120,000 rows × 9 cols, 9.35 MB)
   └── d_positions_fy23.csv (120,000 rows × 9 cols, 9.36 MB)
   └── d_positions_fy24.csv (120,000 rows × 9 cols, 9.36 MB)
   └── d_positions_fy25.csv (120,000 rows × 9 cols, 9.36 MB)

📂 skills_library/
   Files: 6 | Total Size: 108.45 MB | Total Rows: 73,224
   └── meta.csv (1 rows × 2 cols, 0.00 MB)
   └── skills_9.32.csv (34,639 rows × 17 cols, 51.96 MB)
   └── skills_comprehensive_all_versions.csv (38,430 rows × 18 cols, 56.49 MB)
   └── status.csv (1 rows × 2 cols, 0.00 MB)
   └── version_latest.csv (1 rows × 5 cols, 0.00 MB)
   └── versions.csv (152 rows × 1 cols, 0.00 MB)

📂 workforce_context/
   Files: 1 | Total Size: 15.88 MB | Total Rows: 35,000
   └── workforce_context.csv (35,000 rows × 48 cols, 15.88 MB)

📊 DETAILED FILE ANALYSIS
================================================================================

1. data\colleague_positions_history\d_colleague_position_fy22.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\colleague_positions_history\d_colleague_position_fy22.csv
📏 Size: 30.9 MB (32,399,117 bytes)
📅 Modified: 2025-07-17T14:28:58.423135
🔤 Encoding: utf-8
📊 Dimensions: 500,000 rows × 6 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       02/06/2022, 05/05/2022, 07/10/2021 ... (+7 more)
Employee Number                int64           INTEGER         0.0%     52,732   56458214, 56458702, 56459238 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        False, True
Position Start Date            object          VARCHAR(10)     0.0%     754      12/05/2022, 22/07/2021, 14/11/2019 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     500,000  296010023813.0843, 272870049445.15167, 12564902516..
Position Number                int64           INTEGER         0.0%     4,996    50000271, 50002228, 50004214 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 02/06/2022
  Employee Number: 56458214
  Operational: False
  Position Start Date: 12/05/2022
  PosIDLookupKey: 296010023813.0843
  Position Number: 50000271

... and 4 more sample rows available

================================================================================

2. data\colleague_positions_history\d_colleague_position_fy23.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\colleague_positions_history\d_colleague_position_fy23.csv
📏 Size: 31.06 MB (32,572,462 bytes)
📅 Modified: 2025-07-17T14:29:37.568526
🔤 Encoding: utf-8
📊 Dimensions: 500,000 rows × 6 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       02/06/2023, 08/07/2022, 09/06/2023 ... (+7 more)
Employee Number                int64           INTEGER         0.0%     52,555   83068651, 83069298, 83069802 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
Position Start Date            object          VARCHAR(10)     0.0%     754      28/08/2021, 11/02/2021, 02/12/2022 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     500,000  270375578261.5857, 132772848232.61626, 29101808361..
Position Number                int64           INTEGER         0.0%     4,994    50000038, 50002581, 50001484 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 02/06/2023
  Employee Number: 83068651
  Operational: True
  Position Start Date: 28/08/2021
  PosIDLookupKey: 270375578261.5857
  Position Number: 50000038

... and 4 more sample rows available

================================================================================

3. data\colleague_positions_history\d_colleague_position_fy24.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\colleague_positions_history\d_colleague_position_fy24.csv
📏 Size: 31.38 MB (32,900,294 bytes)
📅 Modified: 2025-07-17T14:31:09.801094
🔤 Encoding: utf-8
📊 Dimensions: 500,000 rows × 6 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       01/06/2024, 02/03/2024, 04/05/2024 ... (+7 more)
Employee Number                int64           INTEGER         0.0%     52,457   109582259, 109582324, 109583124 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
Position Start Date            object          VARCHAR(10)     0.0%     754      12/10/2021, 19/08/2023, 16/12/2023 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     500,000  105013205148.2766, 173292809313.289, 167405964612...
Position Number                int64           INTEGER         0.0%     4,992    50000787, 50003316, 50000822 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 01/06/2024
  Employee Number: 109582259
  Operational: True
  Position Start Date: 12/10/2021
  PosIDLookupKey: 105013205148.2766
  Position Number: 50000787

... and 4 more sample rows available

================================================================================

4. data\colleague_positions_history\d_colleague_position_fy25.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\colleague_positions_history\d_colleague_position_fy25.csv
📏 Size: 31.38 MB (32,900,524 bytes)
📅 Modified: 2025-07-17T14:32:15.858814
🔤 Encoding: utf-8
📊 Dimensions: 500,000 rows × 6 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       03/02/2025, 04/11/2024, 05/05/2025 ... (+7 more)
Employee Number                int64           INTEGER         0.0%     52,453   135898158, 135898340, 135898527 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
Position Start Date            object          VARCHAR(10)     0.0%     754      20/02/2024, 10/08/2023, 16/09/2024 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     500,000  190061786802.1381, 148615537635.6917, 214157738853..
Position Number                int64           INTEGER         0.0%     4,995    50000127, 50002154, 50000937 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 03/02/2025
  Employee Number: 135898158
  Operational: True
  Position Start Date: 20/02/2024
  PosIDLookupKey: 190061786802.1381
  Position Number: 50000127

... and 4 more sample rows available

================================================================================

5. data\job_arch_to_positions_mapping\job_arch_to_positions_mapping.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\job_arch_to_positions_mapping\job_arch_to_positions_mapping.csv
📏 Size: 0.09 MB (90,030 bytes)
📅 Modified: 2025-06-10T20:53:47.676582
🔤 Encoding: utf-8
📊 Dimensions: 5,000 rows × 2 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Position_Number                int64           INTEGER         0.0%     5,000    50000000, 50000001, 50000002 ... (+7 more)
JobProfileID                   object          VARCHAR(7)      0.0%     628      R0453.0, R0400.6, R0465.3 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Position_Number: 50000000
  JobProfileID: R0453.0

... and 4 more sample rows available

================================================================================

6. data\job_architecture\job_architecture.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\job_architecture\job_architecture.csv
📏 Size: 0.12 MB (125,628 bytes)
📅 Modified: 2025-06-18T19:21:33.282948
🔤 Encoding: utf-8
📊 Dimensions: 715 rows × 16 columns
✅ Completeness: 88.3%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
JobID                          object          VARCHAR(5)      0.0%     240      R0001, R0002, R0003 ... (+7 more)
Job                            object          VARCHAR(31)     0.0%     35       Payment Systems Anal.., Settlement Officer, Sales ..
JobProfileID                   object          VARCHAR(7)      0.0%     715      R0001.5, R0001.6, R0002.0 ... (+7 more)
JobProfile                     object          VARCHAR(42)     0.0%     309      Payment Systems Anal.., Settlement Officer -.., Sa..
ProfileTitleSuffix             object          VARCHAR(17)     0.0%     16       Senior Manager, Associate, II ... (+7 more)
ManagementLevel                object          VARCHAR(8)      0.0%     8        Group 2, Group 1, Group 4 ... (+5 more)
JobSubFunctionID               object          VARCHAR(6)      0.0%     526      JF0655, JF0559, JF0204 ... (+7 more)
JobSubFunction                 object          VARCHAR(31)     0.0%     110      Data Governance, Machine Learning, Investment Bank..
JobFunctionID                  object          VARCHAR(5)      0.0%     22       JF016, JF012, JF017 ... (+7 more)
JobFunction                    object          VARCHAR(27)     0.0%     22       Data & Analytics, Banking Services, Security & Fra..
JobCategoryID                  object          VARCHAR(4)      0.0%     4        JC2, JC1, JC3 ... (+1 more)
JobCategory                    object          VARCHAR(30)     0.0%     4        Support, Enabling, Revenue Generating ... (+1 more..
Customer Facing                object          VARCHAR(19)     0.7%     2        Customer Facing, Non-Customer Facing
is Banker                      object          VARCHAR(10)     1.0%     2        Non-Banker, Banker
Executive Leadership Group     object          VARCHAR(26)     95.2%    1        Executive Leadership..
Accountability Scope           object          VARCHAR(8)      89.9%    2        Direct, Supports

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  JobID: R0001
  Job: Payment Systems Analyst
  JobProfileID: R0001.5
  JobProfile: Payment Systems Analyst - 5
  ProfileTitleSuffix: Senior Manager
  ManagementLevel: Group 2
  JobSubFunctionID: JF0655
  JobSubFunction: Data Governance
  JobFunctionID: JF016
  JobFunction: Data & Analytics
  JobCategoryID: JC2
  JobCategory: Support
  Customer Facing: Customer Facing
  is Banker: Non-Banker
  Executive Leadership Group: None
  Accountability Scope: None

... and 4 more sample rows available

================================================================================

7. data\job_skill_mapping\job_skill_mapping.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\job_skill_mapping\job_skill_mapping.csv
📏 Size: 1.15 MB (1,205,474 bytes)
📅 Modified: 2025-06-08T12:25:24.030854
🔤 Encoding: utf-8
📊 Dimensions: 40,170 rows × 2 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
JobProfileID                   object          VARCHAR(7)      0.0%     715      R0001.5, R0001.6, R0002.0 ... (+7 more)
Skill_ID                       object          VARCHAR(21)     0.0%     2,091    BGSD16A8EEF4F5775E15, ES147CB8BEA5CF1AF1F6, ES203B..

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  JobProfileID: R0001.5
  Skill_ID: BGSD16A8EEF4F5775E15

... and 4 more sample rows available

================================================================================

8. data\positions_history\d_positions_fy21.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\positions_history\d_positions_fy21.csv
📏 Size: 9.36 MB (9,817,310 bytes)
📅 Modified: 2025-07-17T14:28:28.759280
🔤 Encoding: utf-8
📊 Dimensions: 120,000 rows × 9 columns
✅ Completeness: 85.6%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       01/07/2020, 02/06/2021, 02/12/2020 ... (+7 more)
Position Number                int64           INTEGER         0.0%     4,997    50000000, 50000001, 50000002 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     120,000  173270485187.61182, 133027629035.62636, 2252801223..
Organisational Unit            object          VARCHAR(21)     0.0%     11       Risk Management, Technology, Business Banking ... ..
Cost Centre Number             int64           INTEGER         0.0%     90       2800, 6100, 1500 ... (+7 more)
Position Title                 float64         REAL            100.0%   0        (no data)
People Leader                  float64         REAL            29.8%    23,657   22615063.0, 20703164.0, 23960351.0 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
OrgUnitIDLookupKey             int64           INTEGER         0.0%     119,165  7379873, 5035291, 7975908 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 01/07/2020
  Position Number: 50000000
  PosIDLookupKey: 173270485187.61182
  Organisational Unit: Risk Management
  Cost Centre Number: 2800
  Position Title: None
  People Leader: 22615063.0
  Operational: True
  OrgUnitIDLookupKey: 7379873

... and 4 more sample rows available

================================================================================

9. data\positions_history\d_positions_fy22.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\positions_history\d_positions_fy22.csv
📏 Size: 9.35 MB (9,808,656 bytes)
📅 Modified: 2025-07-17T14:29:11.972782
🔤 Encoding: utf-8
📊 Dimensions: 120,000 rows × 9 columns
✅ Completeness: 85.5%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       01/07/2021, 02/06/2022, 02/09/2021 ... (+7 more)
Position Number                int64           INTEGER         0.0%     4,996    50000000, 50000001, 50000002 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     120,000  103365405326.13818, 186005212604.4463, 20128460902..
Organisational Unit            object          VARCHAR(21)     0.0%     11       Technology, Human Resources, Customer Banking ... ..
Cost Centre Number             int64           INTEGER         0.0%     90       8700, 9500, 7600 ... (+7 more)
Position Title                 float64         REAL            100.0%   0        (no data)
People Leader                  float64         REAL            30.6%    23,512   21927788.0, 25543530.0, 21284128.0 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
OrgUnitIDLookupKey             int64           INTEGER         0.0%     119,221  6388675, 1859562, 8779097 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 01/07/2021
  Position Number: 50000000
  PosIDLookupKey: 103365405326.13818
  Organisational Unit: Technology
  Cost Centre Number: 8700
  Position Title: None
  People Leader: None
  Operational: True
  OrgUnitIDLookupKey: 6388675

... and 4 more sample rows available

================================================================================

10. data\positions_history\d_positions_fy23.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\positions_history\d_positions_fy23.csv
📏 Size: 9.36 MB (9,811,363 bytes)
📅 Modified: 2025-07-17T14:29:47.062044
🔤 Encoding: utf-8
📊 Dimensions: 120,000 rows × 9 columns
✅ Completeness: 85.5%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       01/07/2022, 02/06/2023, 02/09/2022 ... (+7 more)
Position Number                int64           INTEGER         0.0%     4,997    50000000, 50000001, 50000002 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     120,000  229257722889.8355, 273528948555.3892, 236607473829..
Organisational Unit            object          VARCHAR(21)     0.0%     11       Operations, Finance, Business Banking ... (+7 more..
Cost Centre Number             int64           INTEGER         0.0%     90       3500, 8900, 2400 ... (+7 more)
Position Title                 float64         REAL            100.0%   0        (no data)
People Leader                  float64         REAL            30.4%    23,489   26177535.0, 24762376.0, 28631809.0 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
OrgUnitIDLookupKey             int64           INTEGER         0.0%     119,227  2775959, 3327529, 5720406 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 01/07/2022
  Position Number: 50000000
  PosIDLookupKey: 229257722889.8355
  Organisational Unit: Operations
  Cost Centre Number: 3500
  Position Title: None
  People Leader: 26177535.0
  Operational: True
  OrgUnitIDLookupKey: 2775959

... and 4 more sample rows available

================================================================================

11. data\positions_history\d_positions_fy24.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\positions_history\d_positions_fy24.csv
📏 Size: 9.36 MB (9,809,639 bytes)
📅 Modified: 2025-07-17T14:31:41.358159
🔤 Encoding: utf-8
📊 Dimensions: 120,000 rows × 9 columns
✅ Completeness: 85.5%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       03/02/2024, 04/11/2023, 05/08/2023 ... (+7 more)
Position Number                int64           INTEGER         0.0%     4,996    50000000, 50000001, 50000002 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     120,000  273311642539.67545, 267661724949.26575, 1557261226..
Organisational Unit            object          VARCHAR(21)     0.0%     11       Technology, Business Banking, Human Resources ... ..
Cost Centre Number             int64           INTEGER         0.0%     90       8600, 8900, 1300 ... (+7 more)
Position Title                 float64         REAL            100.0%   0        (no data)
People Leader                  float64         REAL            30.4%    23,544   24718683.0, 21972304.0, 29560521.0 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
OrgUnitIDLookupKey             int64           INTEGER         0.0%     119,219  5121237, 8277062, 2023111 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 03/02/2024
  Position Number: 50000000
  PosIDLookupKey: 273311642539.67545
  Organisational Unit: Technology
  Cost Centre Number: 8600
  Position Title: None
  People Leader: 24718683.0
  Operational: True
  OrgUnitIDLookupKey: 5121237

... and 4 more sample rows available

================================================================================

12. data\positions_history\d_positions_fy25.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\positions_history\d_positions_fy25.csv
📏 Size: 9.36 MB (9,813,341 bytes)
📅 Modified: 2025-07-17T14:32:21.706892
🔤 Encoding: utf-8
📊 Dimensions: 120,000 rows × 9 columns
✅ Completeness: 85.5%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     53       01/07/2024, 02/06/2025, 03/02/2025 ... (+7 more)
Position Number                int64           INTEGER         0.0%     4,996    50000000, 50000001, 50000002 ... (+7 more)
PosIDLookupKey                 float64         REAL            0.0%     120,000  183858418477.3336, 146304436475.7278, 199833398427..
Organisational Unit            object          VARCHAR(21)     0.0%     11       Technology, Business Banking, Finance ... (+7 more..
Cost Centre Number             int64           INTEGER         0.0%     90       7900, 1900, 9500 ... (+7 more)
Position Title                 float64         REAL            100.0%   0        (no data)
People Leader                  float64         REAL            30.2%    23,623   29920816.0, 25449314.0, 26874482.0 ... (+7 more)
Operational                    bool            INTEGER         0.0%     2        True, False
OrgUnitIDLookupKey             int64           INTEGER         0.0%     119,219  1061988, 6961677, 7312471 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 01/07/2024
  Position Number: 50000000
  PosIDLookupKey: 183858418477.3336
  Organisational Unit: Technology
  Cost Centre Number: 7900
  Position Title: None
  People Leader: None
  Operational: True
  OrgUnitIDLookupKey: 1061988

... and 4 more sample rows available

================================================================================

13. data\skills_library\meta.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\meta.csv
📏 Size: 0.0 MB (436 bytes)
📅 Modified: 2025-07-11T22:11:57.060620
🔤 Encoding: utf-8
📊 Dimensions: 1 rows × 2 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
attribution                    object          TEXT            0.0%     1        {"body": "Lightcast ..
latestVersion                  float64         REAL            0.0%     1        9.32

📝 SAMPLE DATA (first 1 rows):
------------------------------------------------------------
Row 1:
  attribution: {"body": "Lightcast Skills is an open, comprehensi..
  latestVersion: 9.32

================================================================================

14. data\skills_library\skills_9.32.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\skills_9.32.csv
📏 Size: 51.96 MB (54,486,166 bytes)
📅 Modified: 2025-07-11T22:12:43.569007
🔤 Encoding: utf-8
📊 Dimensions: 34,639 rows × 17 columns
✅ Completeness: 96.7%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
category_id                    int64           INTEGER         0.0%     32       17, 4, 28 ... (+7 more)
category_name                  object          VARCHAR(43)     0.0%     31       Information Technolo.., Architecture and Con.., Pu..
description                    object          TEXT            0.2%     34,561   .NET Assemblies refe.., .NET Code Analysis (.., .N..
descriptionSource              object          VARCHAR(9)      0.0%     1        LIGHTCAST
id                             object          VARCHAR(20)     0.0%     34,639   KS126XS6CQCFGC3NG79X, KS1245X66R9YDDQWP4V3, ES50D0..
infoUrl                        object          VARCHAR(60)     0.0%     34,639   https://lightcast.io.., https://lightcast.io.., ht..
isLanguage                     bool            INTEGER         0.0%     2        False, True
isSoftware                     bool            INTEGER         0.0%     2        True, False
name                           object          VARCHAR(102)    0.0%     34,639   .NET Assemblies, .NET Code Analysis (.., .NET Deve..
subcategory_id                 int64           INTEGER         0.0%     443      442, 476, 474 ... (+7 more)
subcategory_name               object          VARCHAR(52)     0.0%     442      Microsoft Developmen.., Software Development.., So..
tag_wikipediaExtract           object          TEXT            27.7%    21,899   Defined by Microsoft.., FxCop is a free stat.., Th..
tag_wikipediaUrl               object          VARCHAR(159)    28.3%    22,401   https://en.wikipedia.., https://en.wikipedia.., ht..
tags                           object          TEXT            0.0%     23,027   [{"key": "wikipediaE.., [{"key": "wikipediaE.., [{..
type                           object          VARCHAR(42)     0.0%     3        {"id": "ST1", "name".., {"id": "ST3", "name".., {"..
type_id                        object          VARCHAR(3)      0.0%     3        ST1, ST3, ST2
type_name                      object          VARCHAR(17)     0.0%     3        Specialized Skill, Certification, Common Skill

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  category_id: 17
  category_name: Information Technology
  description: .NET Assemblies refer to the compiled code librari..
  descriptionSource: LIGHTCAST
  id: KS126XS6CQCFGC3NG79X
  infoUrl: https://lightcast.io/open-skills/skills/KS126XS6CQ..
  isLanguage: False
  isSoftware: True
  name: .NET Assemblies
  subcategory_id: 442
  subcategory_name: Microsoft Development Tools
  tag_wikipediaExtract: Defined by Microsoft for use in recent versions of..
  tag_wikipediaUrl: https://en.wikipedia.org/wiki/.NET_assemblies
  tags: [{"key": "wikipediaExtract", "value": "\nDefined b..
  type: {"id": "ST1", "name": "Specialized Skill"}
  type_id: ST1
  type_name: Specialized Skill

... and 4 more sample rows available

================================================================================

15. data\skills_library\skills_comprehensive_all_versions.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\skills_comprehensive_all_versions.csv
📏 Size: 56.49 MB (59,237,122 bytes)
📅 Modified: 2025-06-17T19:55:09.224065
🔤 Encoding: utf-8
📊 Dimensions: 38,430 rows × 18 columns
✅ Completeness: 95.4%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
category_id                    float64         REAL            0.6%     33       17.0, 30.0, 21.0 ... (+7 more)
category_name                  object          VARCHAR(43)     8.8%     33       Information Technolo.., Science and Research, Manu..
description                    object          TEXT            3.8%     36,921   Microsoft Sysprep is.., Application Remediat.., Cl..
descriptionSource              object          VARCHAR(85)     3.4%     2,479    LIGHTCAST, https://en.wikipedia.., https://en.wiki..
id                             object          VARCHAR(20)     0.0%     38,430   BGS1024316C916ACCFA3, BGS105C99F084505B956, BGS108..
infoUrl                        object          VARCHAR(60)     0.0%     38,430   https://lightcast.io.., https://lightcast.io.., ht..
isLanguage                     bool            INTEGER         0.0%     2        False, True
isSoftware                     bool            INTEGER         0.0%     2        True, False
name                           object          VARCHAR(102)    0.0%     38,430   DX Spectrum, Microsoft Sysprep, Application Remedi..
source_version                 float64         REAL            0.0%     51       8.5, 9.31, 8.4 ... (+7 more)
subcategory_id                 float64         REAL            0.6%     452      411.0, 476.0, 477.0 ... (+7 more)
subcategory_name               object          VARCHAR(52)     8.8%     459      Enterprise Informati.., Software Development.., So..
tag_wikipediaExtract           object          TEXT            27.8%    24,289   Sysprep is Microsoft.., An assay is an inves.., Ap..
tag_wikipediaUrl               object          VARCHAR(159)    28.4%    24,932   https://en.wikipedia.., https://en.wikipedia.., ht..
tags                           object          TEXT            0.0%     25,593   [], [{"key": "wikipediaE.., [{"key": "wikipediaE....
type                           object          VARCHAR(42)     0.0%     3        {"id": "ST1", "name".., {"id": "ST2", "name".., {"..
type_id                        object          VARCHAR(3)      0.0%     3        ST1, ST2, ST3
type_name                      object          VARCHAR(17)     0.0%     3        Specialized Skill, Common Skill, Certification

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  category_id: 17.0
  category_name: Information Technology
  description: None
  descriptionSource: None
  id: BGS1024316C916ACCFA3
  infoUrl: https://lightcast.io/open-skills/skills/BGS1024316..
  isLanguage: False
  isSoftware: True
  name: DX Spectrum
  source_version: 8.5
  subcategory_id: 411.0
  subcategory_name: Enterprise Information Management
  tag_wikipediaExtract: None
  tag_wikipediaUrl: None
  tags: []
  type: {"id": "ST1", "name": "Specialized Skill"}
  type_id: ST1
  type_name: Specialized Skill

... and 4 more sample rows available

================================================================================

16. data\skills_library\status.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\status.csv
📏 Size: 0.0 MB (50 bytes)
📅 Modified: 2025-07-11T22:11:56.595468
🔤 Encoding: utf-8
📊 Dimensions: 1 rows × 2 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
healthy                        bool            INTEGER         0.0%     1        True
message                        object          VARCHAR(18)     0.0%     1        Service is healthy

📝 SAMPLE DATA (first 1 rows):
------------------------------------------------------------
Row 1:
  healthy: True
  message: Service is healthy

================================================================================

17. data\skills_library\version_latest.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\version_latest.csv
📏 Size: 0.0 MB (1,240 bytes)
📅 Modified: 2025-07-11T22:11:58.107991
🔤 Encoding: utf-8
📊 Dimensions: 1 rows × 5 columns
✅ Completeness: 100.0%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
fields                         object          VARCHAR(132)    0.0%     1        ["subcategory", "cat..
removedSkillCount              int64           INTEGER         0.0%     1        6499
skillCount                     int64           INTEGER         0.0%     1        41138
types                          object          TEXT            0.0%     1        [{"description": "Re..
version                        float64         REAL            0.0%     1        9.32

📝 SAMPLE DATA (first 1 rows):
------------------------------------------------------------
Row 1:
  fields: ["subcategory", "category", "name", "descriptionSo..
  removedSkillCount: 6499
  skillCount: 41138
  types: [{"description": "Removed skills are skills that w..
  version: 9.32

================================================================================

18. data\skills_library\versions.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\skills_library\versions.csv
📏 Size: 0.0 MB (1,186 bytes)
📅 Modified: 2025-07-11T22:11:57.609211
🔤 Encoding: utf-8
📊 Dimensions: 152 rows × 1 columns
✅ Completeness: 100.0%
⚠️  Duplicates: 13 rows

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
version                        float64         REAL            0.0%     139      9.32, 9.31, 9.3 ... (+7 more)

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  version: 9.32

... and 4 more sample rows available

================================================================================

19. data\workforce_context\workforce_context.csv
------------------------------------------------------------
📁 Location: C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\data\workforce_context\workforce_context.csv
📏 Size: 15.88 MB (16,652,326 bytes)
📅 Modified: 2025-06-21T12:31:35.306410
🔤 Encoding: utf-8
📊 Dimensions: 35,000 rows × 48 columns
✅ Completeness: 98.8%

📋 COLUMN ANALYSIS:
Column Name                    Type            DB Type         Nulls    Unique   Sample Values
------------------------------------------------------------------------------------------------------------------------
Week Ending                    object          VARCHAR(10)     0.0%     1        2025-06-21
Bucket                         object          VARCHAR(11)     0.0%     3        New Starter, On Leave, Active
Operational                    object          VARCHAR(3)      0.0%     2        Yes, No
Position Number                int64           INTEGER         0.0%     4,997    50003311, 50003667, 50000226 ... (+7 more)
Position Name                  object          VARCHAR(31)     0.0%     580      Investment Principal.., Operations Vice Pres.., Au..
FTE (raw value in SAP)         float64         REAL            0.0%     4        0.5, 0.6, 0.8 ... (+1 more)
Position Start Date            object          VARCHAR(10)     0.0%     1,697    2020-09-17, 2024-05-05, 2023-12-26 ... (+7 more)
People Leader Flag             object          VARCHAR(17)     0.0%     2        People Leader, Non-People Leader
Salary Group                   object          VARCHAR(8)      0.0%     9        Group 7, Group 2, Group 5 ... (+6 more)
Street                         object          VARCHAR(18)     0.0%     6        259 Queen St, 22 King William St, 2 Carrington St ..
Suburb                         object          VARCHAR(13)     0.0%     6        Brisbane City, Adelaide, Sydney ... (+3 more)
Location                       object          VARCHAR(13)     0.0%     6        Brisbane City, Adelaide, Sydney ... (+3 more)
Rg                             object          VARCHAR(3)      0.0%     5        QLD, SA, NSW ... (+2 more)
Cty                            object          VARCHAR(2)      0.0%     1        AU
Global Region                  object          VARCHAR(12)     0.0%     1        Asia Pacific
Cost ctr                       object          VARCHAR(7)      0.0%     4,862    CC45596, CC35551, CC84958 ... (+7 more)
Cost Center                    object          VARCHAR(16)     0.0%     3,848    Cost Center 6477, Cost Center 5224, Cost Center 34..
Org Unit Number                int64           INTEGER         0.0%     99       2015, 2063, 2052 ... (+7 more)
Org Unit Name                  object          VARCHAR(8)      0.0%     100      Node 024, Node 037, Node 092 ... (+7 more)
ORG_UNIT_NO_1                  int64           INTEGER         0.0%     1        1001
ORG_UNIT_NAME_1                object          VARCHAR(31)     0.0%     1        National Australia B..
ORG_UNIT_NO_2                  int64           INTEGER         0.0%     99       1224, 1250, 1247 ... (+7 more)
ORG_UNIT_NAME_2                object          VARCHAR(33)     0.0%     6        Corporate & Institut.., Technology, NAB Ventures ...
ORG_UNIT_NO_3                  int64           INTEGER         0.0%     99       1329, 1345, 1359 ... (+7 more)
ORG_UNIT_NAME_3                object          VARCHAR(18)     0.0%     10       Technology, Human Resources, Corporate Banking .....
ORG_UNIT_NO_4                  int64           INTEGER         0.0%     99       1435, 1486, 1401 ... (+7 more)
ORG_UNIT_NAME_4                object          VARCHAR(28)     0.0%     10       Business Banking Ope.., Human Resources Stra.., Fi..
ORG_UNIT_NO_5                  int64           INTEGER         0.0%     99       1533, 1511, 1538 ... (+7 more)
ORG_UNIT_NAME_5                object          VARCHAR(7)      0.0%     30       Team 15, Team 05, Team 27 ... (+7 more)
ORG_UNIT_NO_6                  int64           INTEGER         0.0%     99       1691, 1625, 1628 ... (+7 more)
ORG_UNIT_NAME_6                object          VARCHAR(7)      0.0%     26       Squad H, Squad D, Squad S ... (+7 more)
ORG_UNIT_NO_7                  int64           INTEGER         0.0%     99       1708, 1793, 1798 ... (+7 more)
ORG_UNIT_NAME_7                object          VARCHAR(6)      0.0%     20       Pod 15, Pod 19, Pod 9 ... (+7 more)
ORG_UNIT_NO_8                  int64           INTEGER         0.0%     99       1812, 1818, 1844 ... (+7 more)
ORG_UNIT_NAME_8                object          VARCHAR(8)      0.0%     50       Unit 038, Unit 003, Unit 030 ... (+7 more)
ORG_UNIT_NO_9                  int64           INTEGER         0.0%     99       1959, 1923, 1964 ... (+7 more)
ORG_UNIT_NAME_9                object          VARCHAR(7)      0.0%     30       Cell 11, Cell 30, Cell 22 ... (+7 more)
ORG_UNIT_NO_10                 int64           INTEGER         0.0%     99       2015, 2063, 2052 ... (+7 more)
ORG_UNIT_NAME_10               object          VARCHAR(8)      0.0%     100      Node 024, Node 037, Node 092 ... (+7 more)
Employee Number                int64           INTEGER         0.0%     35,000   100000, 100001, 100002 ... (+7 more)
Employee Name                  object          VARCHAR(18)     0.0%     224      Emma Smith, Emma Hernandez, Michael Brown ... (+7 ..
Email Address                  object          VARCHAR(29)     0.0%     224      emma.smith@nab.com.a.., emma.hernandez@nab.c.., mi..
Gender Key                     object          VARCHAR(1)      0.0%     2        F, M
Entry                          object          VARCHAR(11)     0.0%     4        Experienced, Executive, Graduate ... (+1 more)
Employee Group                 object          VARCHAR(10)     0.0%     4        Fixed Term, Permanent, Casual ... (+1 more)
Employee Subgroup              object          VARCHAR(9)      0.0%     3        Full Time, Casual, Part Time
People Leader Number           float64         REAL            29.8%    17,678   110250.0, 132458.0, 102122.0 ... (+7 more)
People Leader Name             object          VARCHAR(18)     29.8%    224      Michelle Hernandez, Andrew Johnson, Jessica Jones ..

📝 SAMPLE DATA (first 5 rows):
------------------------------------------------------------
Row 1:
  Week Ending: 2025-06-21
  Bucket: New Starter
  Operational: Yes
  Position Number: 50003311
  Position Name: Investment Principal Specialist
  FTE (raw value in SAP): 0.5
  Position Start Date: 2020-09-17
  People Leader Flag: People Leader
  Salary Group: Group 7
  Street: 259 Queen St
  Suburb: Brisbane City
  Location: Brisbane City
  Rg: QLD
  Cty: AU
  Global Region: Asia Pacific
  Cost ctr: CC45596
  Cost Center: Cost Center 6477
  Org Unit Number: 2015
  Org Unit Name: Node 024
  ORG_UNIT_NO_1: 1001
  ORG_UNIT_NAME_1: National Australia Bank Limited
  ORG_UNIT_NO_2: 1224
  ORG_UNIT_NAME_2: Corporate & Institutional Banking
  ORG_UNIT_NO_3: 1329
  ORG_UNIT_NAME_3: Technology
  ORG_UNIT_NO_4: 1435
  ORG_UNIT_NAME_4: Business Banking Operations
  ORG_UNIT_NO_5: 1533
  ORG_UNIT_NAME_5: Team 15
  ORG_UNIT_NO_6: 1691
  ORG_UNIT_NAME_6: Squad H
  ORG_UNIT_NO_7: 1708
  ORG_UNIT_NAME_7: Pod 15
  ORG_UNIT_NO_8: 1812
  ORG_UNIT_NAME_8: Unit 038
  ORG_UNIT_NO_9: 1959
  ORG_UNIT_NAME_9: Cell 11
  ORG_UNIT_NO_10: 2015
  ORG_UNIT_NAME_10: Node 024
  Employee Number: 100000
  Employee Name: Emma Smith
  Email Address: emma.smith@nab.com.au
  Gender Key: F
  Entry: Experienced
  Employee Group: Fixed Term
  Employee Subgroup: Full Time
  People Leader Number: 110250.0
  People Leader Name: Michelle Hernandez

... and 4 more sample rows available

================================================================================

📈 SUMMARY STATISTICS
--------------------------------------------------
Total Files Analyzed: 19
Total Data Size: 297.20 MB
Total Rows: 2,754,109
Total Columns: 182
Average Rows per File: 144,953
Average Columns per File: 9

🏆 LARGEST FILES BY ROW COUNT:
1. d_colleague_position_fy22.csv: 500,000 rows
2. d_colleague_position_fy23.csv: 500,000 rows
3. d_colleague_position_fy24.csv: 500,000 rows
4. d_colleague_position_fy25.csv: 500,000 rows
5. d_positions_fy21.csv: 120,000 rows

================================================================================
ANALYSIS COMPLETE
================================================================================