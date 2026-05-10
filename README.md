C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\output\robot-reports\output.xml，为什么出现下面这个定位问题，从截图看到 明明弹出 Enter your pin 页面了，为什么没有进入 “Set or enter PIN” 这个key word? 根本原因是什么？



Env : staging (1.0_001)| Device : Samsung Galaxy S23 | Policy Number: T07776728 | SignIn Successfully With User : docth1@mailsac.com |
 FWD Insurance Flow of My policy(s) Failed due to :Element locator 'android=new UiSelector().text("Insurance")' did not match any elements after 30 seconds

我使用的命令是 
robot `
   -v screenshotDir:"C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\output" `
   -v executionDetailFile:"C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\output\ExecutionDetail.txt" `
   -v udid:"NA" `
   -v deviceName:"Samsung Galaxy S23" `
   -v platformName:"Android" `
   -v platformVersion:"null" `
   -d "C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\output\robot-reports" `
   -o output.xml -r report.html -l log.html `
   "Executor/Insurance/OmneInsuranceExecutor.robot"
PS C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th>

我直接改了，然额还是不行，
根据C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\TestData\TestCases.xlsx, 只运行了TC_03_Ins_TH_Android_ViewPolicy_001，。。。 ,，我看到的页面是页面叫 “Enter your pin” 请你根据 C:\Users\232030\code\GO_OMNE\QRace_Replacement\omne-qa-mob-th\output\robot-reports\output.xml， 分析为什么卡在这里了？ 根因是什么？要怎样修改



TC_03_Ins_TH_Android_ViewPolicy_001
