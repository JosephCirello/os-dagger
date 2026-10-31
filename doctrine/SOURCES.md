# Doctrine sources

Every PDF in this folder was downloaded from the Army Publishing Directorate on 2026-10-30, as the edition that directorate listed as ACTIVE on that date. The SHA-256 is of the file as shipped here; compare it with `sha256sum` if you want to be sure your copy is unaltered.

| Pub | Title | Edition | Status on APD | File | SHA-256 |
|---|---|---|---|---|---|
| ADP 3-0 | Operations | 21 Mar 2025 | ACTIVE | `ADP_3-0_Operations_2025-03-21.pdf` | `ee7e97801f67d8d1d9f630fae1bf3965f75fec7cf6436849a1be3e0134d6235d` |
| ADP 4-0 | Sustainment | 31 Jul 2019, with Change 1 of 18 Aug 2026 | ACTIVE | `ADP_4-0_Sustainment_2019_C1_2026-08-18.pdf` | `ab4fecd5bd8b64434d8567860d009d9390993b7a0f8cb99e72a7c3f97d77cf9d` |
| ADP 5-0 | The Operations Process | 31 Jul 2019 | ACTIVE | `ADP_5-0_The_Operations_Process_2019-07-31.pdf` | `de87305c711536b67cc179fc3d1fefb0711931f68634fe31bbbe8f50604ed963` |
| AR 525-93 | Army Deployment and Redeployment | 15 Apr 2026 | ACTIVE | `AR_525-93_Army_Deployment_and_Redeployment_2026-04-15.pdf` | `b19510c604d68184e6826b73dde69610fdd968f23cb3e53fc4ffdc7786574fe4` |
| AR 600-20 | Army Command Policy | 15 Apr 2026 | ACTIVE | `AR_600-20_Army_Command_Policy_2026-04-15.pdf` | `e1eadd4aeb593c118e653dff4d4142e33af2f1e33353856548977207acd43822` |
| ATP 3-35 | Army Deployment and Redeployment | 9 Mar 2023 | ACTIVE | `ATP_3-35_Army_Deployment_and_Redeployment_2023-03-09.pdf` | `f27a7703327c1ea6a6e10e076e11660cad5512fe7347145bb301b717d31d93e9` |
| ATP 4-16 | Movement Control | 25 Apr 2022 | ACTIVE | `ATP_4-16_Movement_Control_2022-04-25.pdf` | `8a4bec3b6c2e62d324842eac9e32a47b934039a4f6a7bc83edd4297cc6c9732d` |
| FM 4-0 | Sustainment Operations | 20 Mar 2026 | ACTIVE | `FM_4-0_Sustainment_Operations_2026-03-20.pdf` | `90bc9a57f6508a73edd47f1e3a9f0f491e73c1e289da2d32d70c2ca626778d35` |
| FM 5-0 | Planning and Orders Production | 4 Nov 2024, with Change 1 of 11 Aug 2025 | ACTIVE | `FM_5-0_Planning_and_Orders_Production_2024_C1_2025-08-11.pdf` | `d1b5d0e660fd9373954dda356dbbd4f23dcf1d5d173755bb2c9cc95b9d76c774` |
| FM 6-0 | Commander and Staff Organization and Operations | 16 May 2022 | ACTIVE | `FM_6-0_Commander_and_Staff_Organization_and_Operations_2022-05-16.pdf` | `0cb5416178687bf4353b3494bc70f2bb9034bd4627a28bc482a41a9c030b92b2` |

Source: https://armypubs.army.mil (Doctrine and Training, then the ADP, ATP, FM and AR lists). Each file carries its own distribution statement on the title page.

## Not included, and why

- **FM 4-01, Army Transportation Operations.** No longer listed by the Army Publishing Directorate as of 2026-10-30. Transportation now sits inside FM 4-0 (2026), which is included.
- **JP 3-35, Deployment and Redeployment Operations.** The Joint Staff doctrine site now posts only JP 3-0 publicly; the rest of the joint library is on JEL+, which requires a CAC. It is left out rather than shipped from a mirror.

## Adding your own

Drop any PDF into this folder named `SERIES_NUMBER_Title_Words_YYYY-MM-DD.pdf` (for example `ATP_4-43_Petroleum_Supply_Operations_2015-08-06.pdf`) and run `python build_index.py`. The series and number become the citation tag. Keep this table honest: add a row with the edition and the hash.

---

OS DAGGER is a free tool from [Potestas AI](https://potestasai.com).
