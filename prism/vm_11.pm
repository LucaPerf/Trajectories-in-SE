dtmc

module chain
  s : [0..58] init 0;
  // init
  [] s=0 -> 0.14285714285714285:(s'=1) + 0.06666666666666667:(s'=2) + 0.02857142857142857:(s'=3) + 0.02857142857142857:(s'=4) + 0.06666666666666667:(s'=5) + 0.02857142857142857:(s'=6) + 0.02857142857142857:(s'=7) + 0.02857142857142857:(s'=8) + 0.06666666666666667:(s'=9) + 0.02857142857142857:(s'=10) + 0.02857142857142857:(s'=11) + 0.02857142857142857:(s'=12) + 0.06666666666666667:(s'=13) + 0.047619047619047616:(s'=14) + 0.02857142857142857:(s'=15) + 0.02857142857142857:(s'=16) + 0.14285714285714285:(s'=17) + 0.02857142857142857:(s'=18) + 0.02857142857142857:(s'=19) + 0.02857142857142857:(s'=20) + 0.02857142857142857:(s'=21);
  // find [PATH: repository root] -type f -name [PATTERN: Python source files] | xargs grep -l [TERM: target class name] | head [COUNT: small limit],DISCOVERY_REPO
  [] s=1 -> 0.16831683168316833:(s'=5) + 0.32673267326732675:(s'=17) + 0.16831683168316833:(s'=22) + 0.16831683168316833:(s'=23) + 0.16831683168316833:(s'=24);
  // find [PATH: repository root] -type f -name [PATTERN: Python source files] | xargs grep -l [TERM: target class name] | head [COUNT: small limit],DISCOVERY_SOURCE
  [] s=2 -> 0.67:(s'=23) + 0.33:(s'=25);
  // find [PATH: repository root] -type f -name [PATTERN: Python source files] | xargs grep -l [TERM: target format string] | head [COUNT: small limit],DISCOVERY_SOURCE
  [] s=3 -> 1.0:(s'=26);
  // grep -n [TERM: target format string] [PATH: target source file],EMPTY_NONE
  [] s=4 -> 0.25:(s'=17) + 0.25:(s'=47) + 0.25:(s'=52) + 0.25:(s'=55);
  // grep -r [TERM: target format string] [PATH: repository root] --include=[PATTERN: Python source files],DISCOVERY_SOURCE
  [] s=5 -> 0.2:(s'=26) + 0.2:(s'=27) + 0.4:(s'=28) + 0.2:(s'=37);
  // grep -r [TERM: target format string] [PATH: repository root],DISCOVERY_REPO
  [] s=6 -> 1.0:(s'=29);
  // grep -r [TERM: target format string] [PATH: repository root],DISCOVERY_SOURCE
  [] s=7 -> 1.0:(s'=26);
  // grep -r [TERM: target format string] [PATH: top-level package],DISCOVERY_REPO
  [] s=8 -> 1.0:(s'=30);
  // grep -rn [TERM: target format string] [PATH: repository root] --include=[PATTERN: Python source files],DISCOVERY_SOURCE
  [] s=9 -> 0.67:(s'=28) + 0.33:(s'=31);
  // grep -rn [TERM: target format string] [PATH: repository root] | grep -i [TERM: issue keyword],DISCOVERY_SOURCE
  [] s=10 -> 1.0:(s'=32);
  // grep -rn [TERM: target format string] [PATH: repository root] | head [COUNT: small limit],DISCOVERY_SOURCE
  [] s=11 -> 1.0:(s'=27);
  // grep -rn [TERM: target format string] [PATH: repository root],DISCOVERY_REPO
  [] s=12 -> 1.0:(s'=33);
  // grep -rn [TERM: target format string] [PATH: repository root],DISCOVERY_SOURCE
  [] s=13 -> 0.67:(s'=28) + 0.33:(s'=34);
  // grep -rn [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files],DISCOVERY_SOURCE
  [] s=14 -> 0.33:(s'=28) + 0.67:(s'=35);
  // grep -rn [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files],ERROR_NONE
  [] s=15 -> 1.0:(s'=33);
  // grep -rn [TERM: target format string] [PATH: top-level package],DISCOVERY_REPO
  [] s=16 -> 1.0:(s'=33);
  // grep -rn [TERM: target format string] [PATH: top-level package],DISCOVERY_SOURCE
  [] s=17 -> 0.1:(s'=26) + 0.1:(s'=28) + 0.2:(s'=33) + 0.5:(s'=35) + 0.1:(s'=37);
  // grep -rnF [TERM: target format string] [PATH: repository root],DISCOVERY_SOURCE
  [] s=18 -> 1.0:(s'=36);
  // grep -rnF [TERM: target format string] [PATH: repository root],EMPTY_NONE
  [] s=19 -> 1.0:(s'=14);
  // ls -la [PATH: repository root],DISCOVERY_REPO
  [] s=20 -> 1.0:(s'=17);
  // submit_patch [SUMMARY: error message format fix],ERROR_TEST
  [] s=21 -> 0.33333333333333337:(s'=5) + 0.33333333333333337:(s'=49) + 0.33333333333333337:(s'=51);
  // grep -A [COUNT: context lines] [TERM: target class name] [PATH: target source file],DISCOVERY_SOURCE
  [] s=22 -> 0.5:(s'=26) + 0.5:(s'=28);
  // grep -r [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files] | head [COUNT: small limit],DISCOVERY_SOURCE
  [] s=23 -> 0.25:(s'=27) + 0.25:(s'=28) + 0.25:(s'=37) + 0.25:(s'=58);
  // grep -rn [TERM: target format string] [PATH: top-level package] | grep -v [PATTERN: Python cache files],DISCOVERY_SOURCE
  [] s=24 -> 1.0:(s'=33);
  // grep -r [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files],ERROR_NONE
  [] s=25 -> 1.0:(s'=27);
  // grep -n [TERM: target format string] [PATH: target source file],DISCOVERY_SOURCE
  [] s=26 -> 0.16666666666666669:(s'=31) + 0.16666666666666669:(s'=35) + 0.16666666666666669:(s'=39) + 0.16666666666666669:(s'=43) + 0.16666666666666669:(s'=50) + 0.16666666666666669:(s'=57);
  // python3 -c [SCRIPT: fix format string],PROGRESS_PATCH
  [] s=27 -> 0.08080808080808081:(s'=4) + 0.5050505050505051:(s'=38) + 0.08080808080808081:(s'=41) + 0.08080808080808081:(s'=45) + 0.08080808080808081:(s'=46) + 0.17171717171717174:(s'=48);
  // sed -i [SCRIPT: fix format string] [PATH: target source file],PROGRESS_PATCH
  [] s=28 -> 0.04:(s'=21) + 0.04:(s'=27) + 0.69:(s'=38) + 0.04:(s'=44) + 0.04:(s'=47) + 0.15:(s'=48);
  // cat [PATH: target source file] | grep -n -A [COUNT: context lines] -B [COUNT: context lines] [TERM: target format string],DISCOVERY_SOURCE
  [] s=29 -> 1.0:(s'=28);
  // grep -n [TERM: target format string] [PATH: target source file],REPEATED_SOURCE
  [] s=30 -> 0.16831683168316833:(s'=28) + 0.32673267326732675:(s'=30) + 0.16831683168316833:(s'=35) + 0.16831683168316833:(s'=38) + 0.16831683168316833:(s'=43);
  // python3 << [SCRIPT: fix format string],PROGRESS_PATCH
  [] s=31 -> 0.5:(s'=38) + 0.5:(s'=40);
  // grep -rn [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files] | head [COUNT: small limit],DISCOVERY_SOURCE
  [] s=32 -> 1.0:(s'=30);
  // head -n [COUNT: line limit] [PATH: target source file] | tail -n [COUNT: small limit],DISCOVERY_SOURCE
  [] s=33 -> 0.16831683168316833:(s'=27) + 0.6633663366336634:(s'=28) + 0.16831683168316833:(s'=30);
  // cat [PATH: target source file] | sed -n [RANGE: surrounding lines],DISCOVERY_SOURCE
  [] s=34 -> 1.0:(s'=27);
  // sed -n [RANGE: surrounding lines] [PATH: target source file],DISCOVERY_SOURCE
  [] s=35 -> 0.18:(s'=27) + 0.55:(s'=28) + 0.09:(s'=35) + 0.18:(s'=43);
  // cat [PATH: target source file] | head -n [COUNT: line limit] | tail -n [COUNT: small limit],DISCOVERY_SOURCE
  [] s=36 -> 1.0:(s'=27);
  // grep -n -B [COUNT: context lines] -A [COUNT: context lines] [TERM: target format string] [PATH: target source file],DISCOVERY_SOURCE
  [] s=37 -> 0.2:(s'=22) + 0.2:(s'=27) + 0.2:(s'=28) + 0.2:(s'=42) + 0.2:(s'=50);
  // submit_patch [SUMMARY: error message format fix],PROGRESS_TEST__success
  [] s=38 -> 1.0:(s'=38);
  // sed -i [SCRIPT: fix format string] [PATH: target source file]; find [PATH: repository root] -type f -name [PATTERN: locale files] -exec sed -i [SCRIPT: fix format string] [EXEC: find exec placeholder] +,PROGRESS_PATCH
  [] s=39 -> 1.0:(s'=4);
  // submit_patch [SUMMARY: error message format fix],PROGRESS_TEST)__success
  [] s=40 -> 1.0:(s'=40);
  // grep -rn [TERM: target format string] [PATH: top-level package] --include=[PATTERN: Python source files],EMPTY_NONE
  [] s=41 -> 1.0:(s'=38);
  // grep -n -B [COUNT: context lines] -A [COUNT: context lines] [TERM: target format string] [PATH: target source file],REPEATED_SOURCE
  [] s=42 -> 1.0:(s'=37);
  // sed -n [RANGE: surrounding lines] [PATH: target source file],REPEATED_SOURCE
  [] s=43 -> 0.4:(s'=28) + 0.2:(s'=35) + 0.2:(s'=50) + 0.2:(s'=54);
  // grep -n [TERM: target format string] [PATH: target source file] | grep -i [TERM: issue keyword],EMPTY_NONE
  [] s=44 -> 1.0:(s'=27);
  // grep -n [TERM: target format string] [PATH: target source file] | grep -i [TERM: issue keyword] -A [COUNT: context lines] -B [COUNT: context lines],EMPTY_NONE
  [] s=45 -> 1.0:(s'=47);
  // cat [PATH: target source file] | sed -n [RANGE: surrounding lines],PROGRESS_PATCH
  [] s=46 -> 1.0:(s'=38);
  // grep -n [TERM: target format string] [PATH: target source file],PROGRESS_PATCH
  [] s=47 -> 0.33333333333333337:(s'=30) + 0.33333333333333337:(s'=38) + 0.33333333333333337:(s'=41);
  // sed -n [RANGE: surrounding lines] [PATH: target source file],PROGRESS_PATCH
  [] s=48 -> 0.14141414141414144:(s'=28) + 0.7171717171717171:(s'=38) + 0.14141414141414144:(s'=43);
  // python -c [SCRIPT: fix format string],PROGRESS_PATCH
  [] s=49 -> 1.0:(s'=21);
  // sed -i [SCRIPT: fix format string] [PATH: target source file],EMPTY_NONE
  [] s=50 -> 0.33333333333333337:(s'=37) + 0.33333333333333337:(s'=48) + 0.33333333333333337:(s'=56);
  // head -n [COUNT: line limit] [PATH: target source file] | grep -A [COUNT: context lines] [TERM: target class name],EMPTY_NONE
  [] s=51 -> 1.0:(s'=53);
  // grep -nF [TERM: target format string] [PATH: target source file],REPEATED_SOURCE
  [] s=52 -> 1.0:(s'=4);
  // git checkout -- [PATH: target source file] && sed -i [SCRIPT: fix format string] [PATH: target source file] && grep -n [TERM: target format string] [PATH: target source file],PROGRESS_PATCH
  [] s=53 -> 1.0:(s'=38);
  // grep -n [TERM: target format string] [PATH: target source file],ERROR_NONE
  [] s=54 -> 1.0:(s'=38);
  // git checkout -- [PATH: target source file] && python3 -c [SCRIPT: fix format string],PROGRESS_PATCH
  [] s=55 -> 1.0:(s'=38);
  // grep -rn [TERM: target format string] [PATH: repository root] | head [COUNT: small limit],EMPTY_NONE
  [] s=56 -> 1.0:(s'=26);
  // grep -A [COUNT: context lines] [TERM: target class name] [PATH: target source file],EMPTY_NONE
  [] s=57 -> 1.0:(s'=23);
  // grep -rn [TERM: target format string] [PATH: top-level package] | grep -v [PATTERN: Python cache files],EMPTY_NONE
  [] s=58 -> 0.5:(s'=38) + 0.5:(s'=58);
endmodule

label "success" = s=38 | s=40;
label "fail" = false;
label "end" = s=38 | s=40;

rewards "steps"
  true : 1;
endrewards
