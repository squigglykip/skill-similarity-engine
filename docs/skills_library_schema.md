<class 'pandas.core.frame.DataFrame'>
RangeIndex: 38162 entries, 0 to 38161
Data columns (total 12 columns):

 #   Column             Non-Null Count  Dtype  
---  ------             --------------  -----  
 0   Unnamed: 0         38162 non-null  int64  
 1   category           35108 non-null  object 
 2   description        36253 non-null  object 
 3   descriptionSource  27416 non-null  object 
 4   id                 38162 non-null  object 
 5   infoUrl            38162 non-null  object 
 6   isLanguage         38162 non-null  bool   
 7   name               38162 non-null  object 
 8   subcategory        35108 non-null  object 
 9   tags               38162 non-null  object 
10   type               38162 non-null  object 
11   version            38162 non-null  float64

dtypes: bool(1), float64(1), int64(1), object(9)
memory usage: 3.2+ MB

**Example Data**

|   | Unnamed: 0 | category                                    | description                                      | descriptionSource                           | id                   | infoUrl                                               | isLanguage | name                | subcategory                                               | tags                                                     | type                    | version |
|---|------------|---------------------------------------------|--------------------------------------------------|----------------------------------------------|----------------------|--------------------------------------------------------|------------|---------------------|-----------------------------------------------------------|-----------------------------------------------------------|-------------------------|---------|
| 0 | 1226753    | {'id': 17, 'name': 'Information Technology'}| NaN                                              | NaN                                          | BGS1024316GC916ACCF3 | https://lightcast.io/open-skills/skills/BGS102431...   | False      | DX Spectrum         | {'id': 411, 'name': 'Enterprise Information Ma...'}       | [{'id': 517, 'name': 'Specialized Skill'}]               | Specialized Skill        | 8.5     |
| 1 | 2348929    | {'id': 17, 'name': 'Information Technology'}| Sysprep is Microsoft’s System Preparation Tool...| https://en.wikipedia.org/wiki/Sysprep       | BGS105C9F0E4505B956  | https://lightcast.io/open-skills/skills/BGS105C9F...   | False      | Microsoft Sysprep   | {'id': 476, 'name': 'Software Development Tools'}         | [{'key': 'wikipediaExtract', 'value': 'Sysprep...'}]     | {'id': 517, 'name': 'Specialized Skill'} | 9.9     |
| 2 | 2331072    | {'id': 17, 'name': 'Information Technology'}| Application remediation is...                    | NaN                                          | BGS108D01BFCD14A579  | https://lightcast.io/open-skills/skills/BGS108D01...   | False      | Application Remediation | {'id': 378, 'name': 'Software Quality Assurance'}    | []                                                        | {'id': 517, 'name': 'Specialized Skill'} | 9.9     |
| 3 | 2335532    | {'id': 30, 'name': 'Science and Research'}  | An assay is an investigative (analytic) proced...| https://en.wikipedia.org/wiki/Assay         | BGS10A6DE0BB8142E88C | https://lightcast.io/open-skills/skills/BGS10A6DE...   | False      | Clinical Assay       | {'id': 621, 'name': 'Laboratory Research'}              | [{'key': 'wikipediaExtract', 'value': 'An assay...'}]     | {'id': 517, 'name': 'Specialized Skill'} | 9.9     |
| 4 | 2361756    | {'id': 21, 'name': 'Manufacturing and Production'} | Welding is a specialized skill that requires... | NaN                                          | BGS10B5E145CA48862FC | https://lightcast.io/open-skills/skills/BGS10B5E1...   | False      | Welding Tips         | {'id': 542, 'name': 'Welding, Brazing, and So...'}       | []                                                        | {'id': 517, 'name': 'Specialized Skill'} | 9.9     |
