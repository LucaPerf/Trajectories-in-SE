dtmc

module chain
  s : [0..107] init 0;
  // init
  [] s=0 -> 0.03:(s'=1) + 0.27:(s'=2) + 0.13:(s'=3) + 0.07:(s'=4) + 0.07:(s'=5) + 0.03:(s'=6) + 0.1:(s'=7) + 0.07:(s'=8) + 0.03:(s'=9) + 0.03:(s'=10) + 0.03:(s'=11) + 0.07:(s'=12) + 0.07:(s'=13);
  // cat [FILE: relevant source file] | head [COUNT: line limit],INFO_SOURCE
  [] s=1 -> 0.33333333333333337:(s'=8) + 0.33333333333333337:(s'=11) + 0.33333333333333337:(s'=33);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | head [COUNT: small list],DISCOVERY_REPO
  [] s=2 -> 0.2577319587628866:(s'=10) + 0.12371134020618557:(s'=11) + 0.12371134020618557:(s'=14) + 0.12371134020618557:(s'=15) + 0.12371134020618557:(s'=16) + 0.12371134020618557:(s'=17) + 0.12371134020618557:(s'=18);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | head [COUNT: small list],INFO_REPO
  [] s=3 -> 0.25:(s'=1) + 0.5:(s'=8) + 0.25:(s'=19);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target class definition] 2>/dev/null | head [COUNT: small list],DISCOVERY_REPO
  [] s=4 -> 0.5:(s'=20) + 0.5:(s'=21);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target class definition] 2>/dev/null | head [COUNT: small list],DISCOVERY_SOURCE
  [] s=5 -> 0.5:(s'=22) + 0.5:(s'=23);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target class definition],DISCOVERY_REPO
  [] s=6 -> 1.0:(s'=21);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target keyword] | head [COUNT: small list],DISCOVERY_REPO
  [] s=7 -> 0.33333333333333337:(s'=22) + 0.33333333333333337:(s'=24) + 0.33333333333333337:(s'=25);
  // grep -n [PATTERN: target class definition] [FILE: relevant source file],EMPTY_SOURCE
  [] s=8 -> 0.5:(s'=11) + 0.17:(s'=15) + 0.33:(s'=26);
  // grep -r [PATTERN: target class definition] [DIR: repository root] --include=[GLOB: Python source files] -l,DISCOVERY_REPO
  [] s=9 -> 1.0:(s'=22);
  // grep -r [PATTERN: target class definition] [DIR: source package] --include=[GLOB: Python source files],DISCOVERY_SOURCE
  [] s=10 -> 0.25:(s'=22) + 0.25:(s'=27) + 0.25:(s'=32) + 0.25:(s'=38);
  // grep -rn [PATTERN: target class definition] [DIR: source package],DISCOVERY_SOURCE
  [] s=11 -> 0.12371134020618557:(s'=1) + 0.12371134020618557:(s'=24) + 0.12371134020618557:(s'=28) + 0.12371134020618557:(s'=30) + 0.12371134020618557:(s'=31) + 0.2577319587628866:(s'=39) + 0.12371134020618557:(s'=42);
  // ls [DIR: repository root],DISCOVERY_REPO
  [] s=12 -> 0.5:(s'=8) + 0.5:(s'=10);
  // ls [DIR: repository root],INFO_REPO
  [] s=13 -> 0.5:(s'=11) + 0.5:(s'=29);
  // cat [FILE: relevant source file] | grep -A [COUNT: source context lines] [PATTERN: target class definition],EMPTY_SOURCE
  [] s=14 -> 1.0:(s'=15);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] -exec grep -l [PATTERN: target class definition] [ARG: found file] \;,DISCOVERY_SOURCE
  [] s=15 -> 0.33333333333333337:(s'=20) + 0.33333333333333337:(s'=22) + 0.33333333333333337:(s'=31);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] -path [PATH: target package path] | head [COUNT: small list],EMPTY_SOURCE
  [] s=16 -> 1.0:(s'=29);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target class definition],DISCOVERY_SOURCE
  [] s=17 -> 1.0:(s'=31);
  // grep -n [PATTERN: target class definition] [FILE: relevant source file],ERROR_NONE
  [] s=18 -> 1.0:(s'=11);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] -path [PATH: target package path] | head [COUNT: small list],DISCOVERY_REPO
  [] s=19 -> 1.0:(s'=26);
  // grep -n -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file],DISCOVERY_SOURCE
  [] s=20 -> 0.33333333333333337:(s'=33) + 0.33333333333333337:(s'=49) + 0.33333333333333337:(s'=54);
  // head -n [COUNT: line limit] [FILE: relevant source file] | grep -A [COUNT: source context lines] [PATTERN: target class definition],EMPTY_SOURCE
  [] s=21 -> 1.0:(s'=31);
  // cat [FILE: relevant source file] | grep -A [COUNT: source context lines] [PATTERN: target class definition],DISCOVERY_SOURCE
  [] s=22 -> 0.17:(s'=22) + 0.33:(s'=34) + 0.33:(s'=36) + 0.17:(s'=37);
  // cat [FILE: relevant source file] | grep -A [COUNT: source context lines] [PATTERN: target class definition],INFO_SOURCE
  [] s=23 -> 0.49504950495049505:(s'=34) + 0.16831683168316833:(s'=35) + 0.16831683168316833:(s'=71) + 0.16831683168316833:(s'=76);
  // head -n [COUNT: line limit] [FILE: relevant source file] | tail -n [COUNT: line limit],INFO_SOURCE
  [] s=24 -> 0.5:(s'=31) + 0.5:(s'=39);
  // sed -n [RANGE: source line range] [FILE: relevant source file] | head [COUNT: small list],DISCOVERY_SOURCE
  [] s=25 -> 0.33333333333333337:(s'=25) + 0.33333333333333337:(s'=36) + 0.33333333333333337:(s'=37);
  // grep -r [PATTERN: target class definition] [DIR: source package],DISCOVERY_SOURCE
  [] s=26 -> 0.33333333333333337:(s'=25) + 0.33333333333333337:(s'=31) + 0.33333333333333337:(s'=38);
  // cat [FILE: relevant source file] | grep -n -A [COUNT: source context lines] [PATTERN: target class definition],DISCOVERY_SOURCE
  [] s=27 -> 1.0:(s'=34);
  // head -n [COUNT: line limit] [FILE: relevant source file] | tail -n [COUNT: line limit],DISCOVERY_SOURCE
  [] s=28 -> 1.0:(s'=33);
  // grep -rn [PATTERN: target class definition] [DIR: source package] --include=[GLOB: Python source files],DISCOVERY_SOURCE
  [] s=29 -> 0.5:(s'=39) + 0.5:(s'=41);
  // grep -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file],DISCOVERY_SOURCE
  [] s=30 -> 1.0:(s'=40);
  // grep -n [PATTERN: target class definition] [FILE: relevant source file],DISCOVERY_SOURCE
  [] s=31 -> 0.11:(s'=32) + 0.11:(s'=34) + 0.67:(s'=39) + 0.11:(s'=43);
  // grep -n -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file] | head [COUNT: small list],DISCOVERY_SOURCE
  [] s=32 -> 0.33333333333333337:(s'=34) + 0.33333333333333337:(s'=43) + 0.33333333333333337:(s'=65);
  // cat > [FILE: temporary script] << [SCRIPT: patch source file]; python3 [FILE: temporary script],PROGRESS_PATCH
  [] s=33 -> 0.11111111111111112:(s'=20) + 0.11111111111111112:(s'=33) + 0.22222222222222224:(s'=34) + 0.11111111111111112:(s'=36) + 0.11111111111111112:(s'=44) + 0.11111111111111112:(s'=46) + 0.11111111111111112:(s'=52) + 0.11111111111111112:(s'=80);
  // python3 << [SCRIPT: patch source file],PROGRESS_PATCH
  [] s=34 -> 0.010869565217391304:(s'=23) + 0.29347826086956524:(s'=34) + 0.03260869565217391:(s'=39) + 0.10869565217391304:(s'=43) + 0.14130434782608695:(s'=44) + 0.03260869565217391:(s'=48) + 0.03260869565217391:(s'=49) + 0.03260869565217391:(s'=51) + 0.07608695652173914:(s'=54) + 0.010869565217391304:(s'=56) + 0.010869565217391304:(s'=60) + 0.03260869565217391:(s'=61) + 0.010869565217391304:(s'=63) + 0.06521739130434782:(s'=66) + 0.010869565217391304:(s'=67) + 0.010869565217391304:(s'=68) + 0.010869565217391304:(s'=70) + 0.010869565217391304:(s'=72) + 0.010869565217391304:(s'=74) + 0.010869565217391304:(s'=76) + 0.010869565217391304:(s'=77) + 0.010869565217391304:(s'=84) + 0.010869565217391304:(s'=86) + 0.010869565217391304:(s'=92);
  // grep -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file],INFO_SOURCE
  [] s=35 -> 1.0:(s'=34);
  // python3 -c [SCRIPT: patch source file],PROGRESS_PATCH
  [] s=36 -> 0.25252525252525254:(s'=33) + 0.25252525252525254:(s'=34) + 0.08080808080808081:(s'=36) + 0.08080808080808081:(s'=43) + 0.08080808080808081:(s'=44) + 0.25252525252525254:(s'=54);
  // sed -i [SCRIPT: patch source file] [FILE: relevant source file],PROGRESS_PATCH
  [] s=37 -> 0.1:(s'=34) + 0.1:(s'=43) + 0.1:(s'=44) + 0.2:(s'=45) + 0.1:(s'=51) + 0.1:(s'=55) + 0.2:(s'=60) + 0.1:(s'=65);
  // grep -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file] | head [COUNT: output lines],DISCOVERY_SOURCE
  [] s=38 -> 0.5:(s'=47) + 0.5:(s'=53);
  // sed -n [RANGE: source line range] [FILE: relevant source file],DISCOVERY_SOURCE
  [] s=39 -> 0.058823529411764705:(s'=31) + 0.11764705882352941:(s'=33) + 0.1764705882352941:(s'=34) + 0.058823529411764705:(s'=36) + 0.11764705882352941:(s'=37) + 0.1764705882352941:(s'=39) + 0.11764705882352941:(s'=44) + 0.058823529411764705:(s'=48) + 0.058823529411764705:(s'=50) + 0.058823529411764705:(s'=55);
  // grep -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file],REPEATED_SOURCE
  [] s=40 -> 1.0:(s'=34);
  // grep -n -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file] | head [COUNT: small list],EMPTY_SOURCE
  [] s=41 -> 1.0:(s'=49);
  // grep -n -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file],INFO_SOURCE
  [] s=42 -> 1.0:(s'=48);
  // sed -n [RANGE: source line range] [FILE: relevant source file],REPEATED_SOURCE
  [] s=43 -> 0.2871287128712871:(s'=34) + 0.0594059405940594:(s'=36) + 0.0594059405940594:(s'=37) + 0.0594059405940594:(s'=43) + 0.0594059405940594:(s'=46) + 0.0594059405940594:(s'=54) + 0.0594059405940594:(s'=69) + 0.0594059405940594:(s'=72) + 0.0594059405940594:(s'=78) + 0.0594059405940594:(s'=81) + 0.0594059405940594:(s'=88) + 0.0594059405940594:(s'=89) + 0.0594059405940594:(s'=99);
  // submit_patch [PATCH: issue fix],PROGRESS_TEST__success
  [] s=44 -> 1.0:(s'=44);
  // grep -n [PATTERN: keyword] [FILE: relevant source file],PROGRESS_PATCH
  [] s=45 -> 0.33333333333333337:(s'=44) + 0.33333333333333337:(s'=48) + 0.33333333333333337:(s'=59);
  // grep -n [PATTERN: keyword] [FILE: relevant source file] | grep -A [COUNT: source context lines] -B [COUNT: source context lines] [PATTERN: target class definition] | head [COUNT: small list],EMPTY_SOURCE
  [] s=46 -> 0.5:(s'=56) + 0.5:(s'=65);
  // grep -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file] | head [COUNT: output lines],REPEATED_SOURCE
  [] s=47 -> 1.0:(s'=34);
  // sed -n [RANGE: source line range] [FILE: relevant source file],INFO_SOURCE
  [] s=48 -> 0.11111111111111112:(s'=31) + 0.33333333333333337:(s'=34) + 0.11111111111111112:(s'=36) + 0.11111111111111112:(s'=37) + 0.11111111111111112:(s'=44) + 0.11111111111111112:(s'=54) + 0.11111111111111112:(s'=86);
  // grep -n -A [COUNT: source context lines] [PATTERN: target class definition] [FILE: relevant source file] | head [COUNT: small list],REPEATED_SOURCE
  [] s=49 -> 0.25:(s'=34) + 0.25:(s'=43) + 0.25:(s'=44) + 0.25:(s'=48);
  // grep -n [PATTERN: keyword] [FILE: relevant source file],EMPTY_TEST
  [] s=50 -> 1.0:(s'=36);
  // cat [FILE: relevant source file] | sed -n [RANGE: source line range],REPEATED_SOURCE
  [] s=51 -> 0.25:(s'=37) + 0.25:(s'=52) + 0.25:(s'=82) + 0.25:(s'=104);
  // cat [FILE: relevant source file] | sed -n [RANGE: source line range],DISCOVERY_SOURCE
  [] s=52 -> 1.0:(s'=34);
  // cat > [FILE: temporary script] << [SCRIPT: patch source file]; python [FILE: temporary script],PROGRESS_PATCH
  [] s=53 -> 1.0:(s'=45);
  // submit_patch [PATCH: issue fix],ERROR_TEST
  [] s=54 -> 0.22772277227722773:(s'=34) + 0.07920792079207921:(s'=36) + 0.07920792079207921:(s'=57) + 0.37623762376237624:(s'=58) + 0.07920792079207921:(s'=62) + 0.07920792079207921:(s'=69) + 0.07920792079207921:(s'=74);
  // grep -n [PATTERN: keyword] [FILE: relevant source file] | head [COUNT: small list],DISCOVERY_SOURCE
  [] s=55 -> 0.5:(s'=36) + 0.5:(s'=37);
  // cat [FILE: relevant source file] | grep -n -A [COUNT: source context lines] [PATTERN: target class definition],REPEATED_SOURCE
  [] s=56 -> 0.33333333333333337:(s'=44) + 0.33333333333333337:(s'=75) + 0.33333333333333337:(s'=90);
  // python3 -c [SCRIPT: patch source file],ERROR_NONE
  [] s=57 -> 1.0:(s'=32);
  // cat [FILE: relevant test file],ERROR_TEST
  [] s=58 -> 0.49504950495049505:(s'=34) + 0.16831683168316833:(s'=37) + 0.16831683168316833:(s'=61) + 0.16831683168316833:(s'=83);
  // grep -B [COUNT: source context lines] -A [COUNT: source context lines] [PATTERN: target method definition] [FILE: relevant source file] | head [COUNT: small list],DISCOVERY_SOURCE
  [] s=59 -> 1.0:(s'=64);
  // sed -n [RANGE: source line range] [FILE: relevant source file],PROGRESS_PATCH
  [] s=60 -> 0.4:(s'=34) + 0.4:(s'=44) + 0.2:(s'=54);
  // find [DIR: test directory] -name [GLOB: relevant test files],DISCOVERY_TEST
  [] s=61 -> 0.25:(s'=23) + 0.25:(s'=34) + 0.25:(s'=43) + 0.25:(s'=60);
  // cat [FILE: relevant test file],ERROR_NONE
  [] s=62 -> 1.0:(s'=36);
  // cat [FILE: relevant source file] | sed -n [RANGE: source line range],INFO_SOURCE
  [] s=63 -> 0.5:(s'=34) + 0.5:(s'=91);
  // grep -B [COUNT: source context lines] -A [COUNT: source context lines] [PATTERN: target method definition] [FILE: relevant source file] | head [COUNT: small list],REPEATED_SOURCE
  [] s=64 -> 1.0:(s'=44);
  // grep -rn [PATTERN: target keyword] [FILE: relevant test file] 2>/dev/null || echo [MESSAGE: fallback message],EMPTY_TEST
  [] s=65 -> 0.67:(s'=44) + 0.33:(s'=60);
  // cat [FILE: relevant source file] | grep -A [COUNT: source context lines] [PATTERN: target class definition],REPEATED_SOURCE
  [] s=66 -> 0.5:(s'=23) + 0.25:(s'=44) + 0.25:(s'=103);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | tail [COUNT: output lines],ERROR_TEST
  [] s=67 -> 0.5:(s'=73) + 0.5:(s'=105);
  // cat [FILE: relevant test file],REPEATED_ERROR_TEST
  [] s=68 -> 1.0:(s'=56);
  // python3 << [SCRIPT: patch source file],INFO_SOURCE
  [] s=69 -> 0.5:(s'=34) + 0.5:(s'=95);
  // cd [DIR: repository root] && python -m django test [TESTS: relevant test modules] --settings=[SETTINGS: test settings] -v2 2>&1,ERROR_TEST
  [] s=70 -> 0.5:(s'=34) + 0.5:(s'=44);
  // grep -B [COUNT: source context lines] -A [COUNT: source context lines] [PATTERN: target method definition] [FILE: relevant source file] | head [COUNT: small list],INFO_SOURCE
  [] s=71 -> 1.0:(s'=34);
  // python3 [SCRIPT: test runner] [TESTS: relevant test modules] --verbosity=[COUNT: verbose level],ERROR_TEST
  [] s=72 -> 0.5:(s'=39) + 0.5:(s'=94);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | tail [COUNT: output lines],REPEATED_ERROR_TEST
  [] s=73 -> 1.0:(s'=48);
  // sed -n [RANGE: source line range] [FILE: relevant source file],ERROR_NONE
  [] s=74 -> 0.5:(s'=34) + 0.5:(s'=42);
  // find [DIR: test directory] -name [GLOB: relevant test files] 2>/dev/null; find [DIR: test directory] -path [PATH: target package path] -name [GLOB: Python source files] | head [COUNT: small list],DISCOVERY_TEST
  [] s=75 -> 1.0:(s'=44);
  // submit_patch [PATCH: issue fix],REPEATED_ERROR_TEST
  [] s=76 -> 0.5:(s'=34) + 0.5:(s'=58);
  // submit_patch [PATCH: issue fix],ERROR_NONE
  [] s=77 -> 1.0:(s'=54);
  // cd [DIR: repository root] && python -m django test [TESTS: relevant test modules] --settings=[SETTINGS: test settings] -v2 2>&1 | head [COUNT: output lines],ERROR_TEST
  [] s=78 -> 1.0:(s'=79);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1,ERROR_NONE
  [] s=79 -> 1.0:(s'=81);
  // cd [DIR: repository root] && git checkout -- [FILE: relevant source file],PROGRESS_PATCH
  [] s=80 -> 1.0:(s'=39);
  // cat [FILE: relevant test file],DISCOVERY_TEST
  [] s=81 -> 0.33333333333333337:(s'=34) + 0.33333333333333337:(s'=37) + 0.33333333333333337:(s'=70);
  // grep -rn [PATTERN: target class definition] [DIR: source package] --include=[GLOB: Python source files],DISCOVERY_TEST
  [] s=82 -> 1.0:(s'=85);
  // grep -rn [PATTERN: target keyword] [FILE: relevant test file] 2>/dev/null || echo [MESSAGE: fallback message],DISCOVERY_TEST
  [] s=83 -> 1.0:(s'=43);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1,ERROR_TEST
  [] s=84 -> 0.33333333333333337:(s'=87) + 0.33333333333333337:(s'=96) + 0.33333333333333337:(s'=97);
  // cat [FILE: relevant source file] | sed -n [RANGE: source line range],ERROR_NONE
  [] s=85 -> 1.0:(s'=63);
  // cat [FILE: relevant test file],EMPTY_TEST
  [] s=86 -> 0.5:(s'=23) + 0.5:(s'=61);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] -path [PATH: target package path] | head [COUNT: small list],DISCOVERY_TEST
  [] s=87 -> 1.0:(s'=43);
  // grep -rn [PATTERN: target class definition] [DIR: source package],DISCOVERY_TEST
  [] s=88 -> 1.0:(s'=34);
  // grep -n [PATTERN: keyword] [FILE: relevant source file],ERROR_NONE
  [] s=89 -> 1.0:(s'=43);
  // submit_patch [PATCH: issue fix],PROGRESS_TEST)__success
  [] s=90 -> 1.0:(s'=90);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | head [COUNT: output lines],ERROR_TEST
  [] s=91 -> 0.5:(s'=84) + 0.5:(s'=93);
  // grep -n [PATTERN: keyword] [FILE: relevant source file],INFO_SOURCE
  [] s=92 -> 1.0:(s'=48);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | head [COUNT: small list],DISCOVERY_TEST
  [] s=93 -> 1.0:(s'=96);
  // ls -la [DIR: test subdirectory] 2>/dev/null || ls -la [DIR: test directory] | head [COUNT: small list],DISCOVERY_REPO
  [] s=94 -> 1.0:(s'=44);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] | xargs grep -l [PATTERN: target class definition] 2>/dev/null | head [COUNT: small list],DISCOVERY_TEST
  [] s=95 -> 1.0:(s'=44);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | head [COUNT: output lines],PROGRESS_TEST
  [] s=96 -> 0.5:(s'=84) + 0.5:(s'=102);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1,REPEATED_ERROR_TEST
  [] s=97 -> 1.0:(s'=98);
  // python3 -c [SCRIPT: patch source file],ERROR_TEST
  [] s=98 -> 1.0:(s'=100);
  // find [DIR: repository root] -type f -name [GLOB: Python source files] -exec grep -l [PATTERN: target class definition] [ARG: found file] \;,EMPTY_TEST
  [] s=99 -> 1.0:(s'=101);
  // python3 -c [SCRIPT: patch source file],REPEATED_ERROR_TEST
  [] s=100 -> 1.0:(s'=102);
  // grep -n [PATTERN: keyword] [FILE: relevant source file] | head [COUNT: small list],EMPTY_SOURCE
  [] s=101 -> 1.0:(s'=81);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | tail [COUNT: output lines],PROGRESS_TEST
  [] s=102 -> 0.5:(s'=51) + 0.5:(s'=91);
  // python3 << [SCRIPT: patch source file],DISCOVERY_TEST
  [] s=103 -> 1.0:(s'=34);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1,PROGRESS_TEST
  [] s=104 -> 1.0:(s'=67);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1 | tail [COUNT: output lines],REPEATED_TEST
  [] s=105 -> 1.0:(s'=106);
  // cd [DIR: repository root] && python [SCRIPT: test runner] [TESTS: relevant test modules] -v2 2>&1,REPEATED_TEST
  [] s=106 -> 1.0:(s'=107);
  // submit_patch [PATCH: issue fix],PROGRESS_PATCH__success
  [] s=107 -> 1.0:(s'=107);
endmodule

label "success" = s=44 | s=90 | s=107;
label "fail" = false;
label "end" = s=44 | s=90 | s=107;

rewards "steps"
  true : 1;
endrewards
