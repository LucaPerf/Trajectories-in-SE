dtmc

module chain
  s : [0..119] init 0;
  // init
  [] s=0 -> 0.19191919191919193:(s'=1) + 0.06060606060606061:(s'=2) + 0.06060606060606061:(s'=3) + 0.19191919191919193:(s'=4) + 0.31313131313131315:(s'=5) + 0.06060606060606061:(s'=6) + 0.06060606060606061:(s'=7) + 0.06060606060606061:(s'=8);
  // ,__success
  [] s=1 -> 1.0:(s'=1);
  // DISCOVERY_REPO,DISCOVERY_SOURCE
  [] s=2 -> 1.0:(s'=9);
  // find [PATH: repository root] -name [FILE: target source file] -path [PATTERN: nested path pattern],DISCOVERY_REPO
  [] s=3 -> 1.0:(s'=10);
  // find [PATH: repository root] -type f -name [PATTERN: python files] | xargs grep -l [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_REPO
  [] s=4 -> 0.67:(s'=11) + 0.33:(s'=12);
  // find [PATH: repository root] -type f -name [PATTERN: python files] | xargs grep -l [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=5 -> 0.17:(s'=10) + 0.83:(s'=11);
  // find [PATH: repository root] -type f -name [PATTERN: python files] | xargs grep -l [PATTERN: optimization keywords] | head -[COUNT: display limit],EMPTY_NONE
  [] s=6 -> 1.0:(s'=13);
  // grep -r -n -A [COUNT: context lines] [PATTERN: class definition] [PATH: source file],DISCOVERY_SOURCE
  [] s=7 -> 1.0:(s'=14);
  // ls [PATH: repository root],DISCOVERY_REPO
  [] s=8 -> 1.0:(s'=15);
  // DISCOVERY_SOURCE,DISCOVERY_SOURCE
  [] s=9 -> 0.55:(s'=9) + 0.09:(s'=29) + 0.09:(s'=75) + 0.09:(s'=87) + 0.09:(s'=102) + 0.09:(s'=110);
  // cat [PATH: source file],DISCOVERY_SOURCE
  [] s=10 -> 0.2:(s'=10) + 0.2:(s'=12) + 0.2:(s'=16) + 0.2:(s'=46) + 0.2:(s'=48);
  // cat [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=11 -> 0.17346938775510207:(s'=11) + 0.0816326530612245:(s'=16) + 0.0816326530612245:(s'=17) + 0.17346938775510207:(s'=19) + 0.0816326530612245:(s'=20) + 0.0816326530612245:(s'=21) + 0.0816326530612245:(s'=30) + 0.0816326530612245:(s'=32) + 0.0816326530612245:(s'=54) + 0.0816326530612245:(s'=78);
  // grep -n [PATTERN: method definition] [PATH: source file],DISCOVERY_SOURCE
  [] s=12 -> 0.33333333333333337:(s'=18) + 0.33333333333333337:(s'=28) + 0.33333333333333337:(s'=42);
  // find [PATH: repository root] -type f -name [FILE: target source file] | grep -i [PATTERN: target path],ERROR_NONE
  [] s=13 -> 1.0:(s'=5);
  // grep -r -n -A [COUNT: context lines] [PATTERN: method definition] [PATH: source file],DISCOVERY_SOURCE
  [] s=14 -> 1.0:(s'=22);
  // cat [PATH: source file],ERROR_NONE
  [] s=15 -> 1.0:(s'=23);
  // cat [PATH: source file] | head -[COUNT: display limit],REPEATED_SOURCE
  [] s=16 -> 0.5:(s'=11) + 0.5:(s'=24);
  // cat [PATH: test file] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=17 -> 0.33333333333333337:(s'=11) + 0.33333333333333337:(s'=37) + 0.33333333333333337:(s'=60);
  // grep -n [PATTERN: class and method] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=18 -> 1.0:(s'=25);
  // cat [PATH: source file] | tail -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=19 -> 0.5:(s'=21) + 0.5:(s'=26);
  // grep -n [PATTERN: method name] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=20 -> 0.5:(s'=20) + 0.5:(s'=21);
  // python3 << [MARKER: script end] [SCRIPT: apply fix],PROGRESS_PATCH
  [] s=21 -> 0.2:(s'=27) + 0.2:(s'=35) + 0.2:(s'=38) + 0.4:(s'=43);
  // grep -n -A [COUNT: context lines] [PATTERN: method definition] [PATH: source file],DISCOVERY_SOURCE
  [] s=22 -> 1.0:(s'=21);
  // find [PATH: repository root] -type f -name [FILE: target source file],DISCOVERY_SOURCE
  [] s=23 -> 1.0:(s'=10);
  // head -[COUNT: display limit] [PATH: source file],DISCOVERY_TEST
  [] s=24 -> 1.0:(s'=31);
  // grep -n -A [COUNT: context lines] [PATTERN: class definition] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=25 -> 0.5:(s'=33) + 0.5:(s'=37);
  // cat [PATH: source file] | grep -n -A [COUNT: context lines] [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=26 -> 0.33333333333333337:(s'=34) + 0.33333333333333337:(s'=80) + 0.33333333333333337:(s'=95);
  // python3 << [MARKER: script end] [SCRIPT: inspect source],DISCOVERY_SOURCE
  [] s=27 -> 1.0:(s'=36);
  // sed -n [RANGE: relevant lines] [PATH: source file],DISCOVERY_SOURCE
  [] s=28 -> 0.33333333333333337:(s'=25) + 0.33333333333333337:(s'=28) + 0.33333333333333337:(s'=37);
  // ERROR_NONE,ERROR_NONE
  [] s=29 -> 1.0:(s'=9);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=30 -> 1.0:(s'=39);
  // cat -n [PATH: source file] | head -[COUNT: display limit] | tail -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=31 -> 1.0:(s'=10);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition],DISCOVERY_SOURCE
  [] s=32 -> 0.33333333333333337:(s'=40) + 0.33333333333333337:(s'=78) + 0.33333333333333337:(s'=82);
  // grep -n -A [COUNT: context lines] [PATTERN: class definition] [PATH: source file] | head -[COUNT: display limit],REPEATED_SOURCE
  [] s=33 -> 1.0:(s'=28);
  // python3 -c [SCRIPT: apply fix],PROGRESS_PATCH
  [] s=34 -> 0.33333333333333337:(s'=41) + 0.33333333333333337:(s'=43) + 0.33333333333333337:(s'=62);
  // python3 -c [SCRIPT: reproduce optimizer issue],PROGRESS_ISSUE
  [] s=35 -> 1.0:(s'=42);
  // cat [PATH: source file] | sed -n [RANGE: relevant lines],REPEATED_SOURCE
  [] s=36 -> 1.0:(s'=44);
  // sed -n [RANGE: relevant lines] [PATH: source file],REPEATED_SOURCE
  [] s=37 -> 0.09:(s'=21) + 0.09:(s'=34) + 0.55:(s'=37) + 0.09:(s'=63) + 0.09:(s'=72) + 0.09:(s'=88);
  // cd [PATH: repository root] && python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity],ERROR_NONE
  [] s=38 -> 1.0:(s'=45);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition] | tail -[COUNT: display limit],REPEATED_SOURCE
  [] s=39 -> 1.0:(s'=47);
  // cat [PATH: source file],REPEATED_SOURCE
  [] s=40 -> 1.0:(s'=49);
  // cat [PATH: source file] | grep -n -A [COUNT: context lines] [PATTERN: method definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=41 -> 1.0:(s'=50);
  // grep -A [COUNT: context lines] [PATTERN: method definition] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=42 -> 0.5:(s'=48) + 0.5:(s'=51);
  // sed -n [RANGE: relevant lines] [PATH: source file],PROGRESS_PATCH
  [] s=43 -> 0.25:(s'=52) + 0.25:(s'=77) + 0.5:(s'=109);
  // python3 -m pytest [PATH: test file] -v 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=44 -> 0.5:(s'=53) + 0.5:(s'=96);
  // find [PATH: repository root] -name [FILE: test runner] -o -name [FILE: setup file] | head -[COUNT: display limit],DISCOVERY_REPO
  [] s=45 -> 1.0:(s'=55);
  // head -[COUNT: display limit] [PATH: source file],REPEATED_SOURCE
  [] s=46 -> 1.0:(s'=34);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: method definition],ERROR_NONE
  [] s=47 -> 1.0:(s'=12);
  // cat -n [PATH: source file] | sed -n [RANGE: relevant lines],DISCOVERY_SOURCE
  [] s=48 -> 0.33333333333333337:(s'=48) + 0.11111111111111112:(s'=56) + 0.22222222222222224:(s'=63) + 0.11111111111111112:(s'=76) + 0.11111111111111112:(s'=92) + 0.11111111111111112:(s'=114);
  // grep -A [COUNT: context lines] [PATTERN: class definition] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=49 -> 1.0:(s'=57);
  // cat [PATH: source file] | grep -n -A [COUNT: context lines] [PATTERN: method definition] | head -[COUNT: display limit],REPEATED_SOURCE
  [] s=50 -> 1.0:(s'=51);
  // find [PATH: repository root] -type f -name [PATTERN: python files] | xargs grep -l [PATTERN: optimization keywords] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=51 -> 0.5:(s'=17) + 0.5:(s'=65);
  // find [PATH: tests directory] -type f -name [PATTERN: python files] | xargs grep -l [PATTERN: optimization keywords] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=52 -> 0.5:(s'=58) + 0.5:(s'=90);
  // python3 -c [SCRIPT: configure django],EMPTY_NONE
  [] s=53 -> 1.0:(s'=59);
  // grep -n -A [COUNT: context lines] [PATTERN: method definition] [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition] -A [COUNT: context lines] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=54 -> 1.0:(s'=60);
  // python3 << [MARKER: script end] [SCRIPT: inspect source],PROGRESS_PATCH
  [] s=55 -> 1.0:(s'=61);
  // cat [PATH: test file] | grep -n -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: class name] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=56 -> 1.0:(s'=63);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: method definition],DISCOVERY_SOURCE
  [] s=57 -> 0.5:(s'=44) + 0.5:(s'=64);
  // python -m pytest [PATH: test file] -xvs 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=58 -> 0.5:(s'=66) + 0.5:(s'=109);
  // python3 -c [SCRIPT: reproduce optimizer issue],ERROR_NONE
  [] s=59 -> 1.0:(s'=67);
  // grep -n [PATTERN: class name] [PATH: test file] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=60 -> 0.5:(s'=32) + 0.5:(s'=68);
  // python3 << [MARKER: script end] [SCRIPT: inspect source],REPEATED_SOURCE
  [] s=61 -> 1.0:(s'=69);
  // python3 -c [SCRIPT: inspect source],DISCOVERY_SOURCE
  [] s=62 -> 1.0:(s'=70);
  // cat -n [PATH: source file] | sed -n [RANGE: relevant lines],REPEATED_SOURCE
  [] s=63 -> 0.09090909090909091:(s'=37) + 0.09090909090909091:(s'=48) + 0.27272727272727276:(s'=63) + 0.36363636363636365:(s'=83) + 0.09090909090909091:(s'=84) + 0.09090909090909091:(s'=98);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: class definition],DISCOVERY_SOURCE
  [] s=64 -> 1.0:(s'=71);
  // submit_patch [PATCH_SUMMARY: reduce repeated field migrations],PROGRESS_TEST__success
  [] s=65 -> 1.0:(s'=65);
  // python -m django test [MODULE: test module] --settings=[SETTINGS: settings module] 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=66 -> 0.33333333333333337:(s'=17) + 0.33333333333333337:(s'=66) + 0.33333333333333337:(s'=116);
  // python3 -c [SCRIPT: reproduce optimizer issue],PROGRESS_PATCH
  [] s=67 -> 1.0:(s'=73);
  // grep -n [PATTERN: method definition] [PATH: source file] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=68 -> 1.0:(s'=26);
  // cd [PATH: repository root] && python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=69 -> 1.0:(s'=74);
  // grep -r [PATTERN: class name] [PATH: test file] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=70 -> 1.0:(s'=32);
  // cat -n [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=71 -> 1.0:(s'=63);
  // cat > [PATH: temporary script] << [MARKER: script end] [SCRIPT: apply fix] python3 [PATH: temporary script],PROGRESS_PATCH
  [] s=72 -> 1.0:(s'=77);
  // python3 -m django test [MODULE: test module] --settings=[SETTINGS: settings module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=73 -> 1.0:(s'=79);
  // cd [PATH: repository root] && python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],REPEATED_TEST
  [] s=74 -> 1.0:(s'=81);
  // DISCOVERY_REPO,EMPTY_TEST
  [] s=75 -> 1.0:(s'=9);
  // grep -n [PATTERN: method name] [PATH: test file] | head -[COUNT: display limit],EMPTY_TEST
  [] s=76 -> 1.0:(s'=63);
  // submit_patch [PATCH_SUMMARY: reduce repeated field migrations],PROGRESS_PATCH__success
  [] s=77 -> 1.0:(s'=77);
  // DISCOVERY_SOURCE,ERROR_NONE
  [] s=78 -> 0.25:(s'=11) + 0.5:(s'=78) + 0.25:(s'=104);
  // find [PATH: tests directory] -name [PATTERN: settings files] -o -name [PATTERN: settings files] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=79 -> 1.0:(s'=85);
  // cat [PATH: source file] | head -[COUNT: display limit] | tail -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=80 -> 1.0:(s'=86);
  // find [PATH: tests directory] -name [PATTERN: optimizer or migration] -o -name [PATTERN: optimizer or migration] | grep -i [PATTERN: test] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=81 -> 1.0:(s'=52);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [PATTERN: class definition],REPEATED_SOURCE
  [] s=82 -> 1.0:(s'=57);
  // sed -i [SCRIPT: apply fix] [PATH: source file],PROGRESS_PATCH
  [] s=83 -> 0.16831683168316833:(s'=37) + 0.16831683168316833:(s'=43) + 0.16831683168316833:(s'=48) + 0.16831683168316833:(s'=63) + 0.32673267326732675:(s'=98);
  // grep -n -A [COUNT: context lines] [PATTERN: optimization keywords] [PATH: test file] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=84 -> 1.0:(s'=48);
  // python3 -m django test [MODULE: test module] --settings=[SETTINGS: settings module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],REPEATED_TEST
  [] s=85 -> 1.0:(s'=89);
  // cat > [PATH: temporary script] << [MARKER: script end] [SCRIPT: apply fix] python3 [PATH: temporary script],ERROR_PATCH
  [] s=86 -> 1.0:(s'=26);
  // REPEATED_SOURCE,REPEATED_SOURCE
  [] s=87 -> 0.6:(s'=87) + 0.2:(s'=91) + 0.2:(s'=115);
  // cd [PATH: repository root] && python -c [SCRIPT: reproduce optimizer issue],ERROR_NONE
  [] s=88 -> 1.0:(s'=93);
  // python3 [PATH: test runner] [MODULE: test module] --verbosity=[COUNT: verbosity] 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=89 -> 0.5:(s'=94) + 0.5:(s'=113);
  // cd [PATH: repository root] && python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],PROGRESS_TEST
  [] s=90 -> 1.0:(s'=77);
  // ERROR_PATCH,ERROR_PATCH
  [] s=91 -> 1.0:(s'=97);
  // cat [PATH: test file] | head -[COUNT: display limit],REPEATED_TEST
  [] s=92 -> 1.0:(s'=63);
  // cd [PATH: repository root] && python -c [SCRIPT: reproduce optimizer issue],PROGRESS_ISSUE
  [] s=93 -> 1.0:(s'=65);
  // python3 -m django test [MODULE: test module] -v [COUNT: verbosity] 2>&1 | head -[COUNT: display limit],REPEATED_TEST
  [] s=94 -> 1.0:(s'=99);
  // cat [PATH: source file] | grep -n -A [COUNT: context lines] [PATTERN: class definition] | head -[COUNT: display limit],REPEATED_SOURCE
  [] s=95 -> 1.0:(s'=100);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: method definition] | tail -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=96 -> 1.0:(s'=101);
  // PROGRESS_PATCH,PROGRESS_PATCH
  [] s=97 -> 0.5:(s'=77) + 0.5:(s'=102);
  // cat -n [PATH: source file] | sed -n [RANGE: relevant lines],PROGRESS_PATCH
  [] s=98 -> 0.33333333333333337:(s'=65) + 0.33333333333333337:(s'=77) + 0.33333333333333337:(s'=103);
  // python3 -c [SCRIPT: run optimizer tests] 2>&1 | tail -[COUNT: display limit],REPEATED_TEST
  [] s=99 -> 1.0:(s'=105);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: optimization keywords],PROGRESS_PATCH
  [] s=100 -> 1.0:(s'=77);
  // python3 -m [MODULE: test module] 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=101 -> 1.0:(s'=106);
  // REPEATED_SOURCE,EMPTY_NONE
  [] s=102 -> 0.25:(s'=9) + 0.25:(s'=87) + 0.5:(s'=102);
  // cat -n [PATH: source file] | sed -n [RANGE: relevant lines],REPEATED_PATCH
  [] s=103 -> 1.0:(s'=107);
  // DISCOVERY_SOURCE,EMPTY_NONE
  [] s=104 -> 1.0:(s'=9);
  // python3 -c [SCRIPT: reproduce optimizer issue],REPEATED_PATCH
  [] s=105 -> 1.0:(s'=65);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [PATTERN: optimization keywords],DISCOVERY_SOURCE
  [] s=106 -> 1.0:(s'=108);
  // submit_patch [PATCH_SUMMARY: reduce repeated field migrations],ERROR_PATCH
  [] s=107 -> 1.0:(s'=109);
  // python3 -c [SCRIPT: inspect environment],INFO_NONE
  [] s=108 -> 1.0:(s'=111);
  // sed -n [RANGE: relevant lines] [PATH: source file],REPEATED_PATCH
  [] s=109 -> 0.1:(s'=58) + 0.1:(s'=83) + 0.1:(s'=90) + 0.6:(s'=109) + 0.1:(s'=112);
  // cat -n [PATH: source file] | grep -n -A [COUNT: context lines] [PATTERN: class definition] | head -[COUNT: display limit],DISCOVERY_SOURCE
  [] s=110 -> 1.0:(s'=48);
  // python3 [PATH: test file] 2>&1 | tail -[COUNT: display limit],ERROR_TEST
  [] s=111 -> 1.0:(s'=89);
  // cat -n [PATH: source file] | sed -n [RANGE: relevant lines],ERROR_PATCH
  [] s=112 -> 1.0:(s'=83);
  // python3 [PATH: test runner] [MODULE: test module] --verbosity=[COUNT: verbosity] 2>&1 | head -[COUNT: display limit],PROGRESS_TEST
  [] s=113 -> 1.0:(s'=77);
  // python -m pytest [PATH: test file] -v 2>&1 | head -[COUNT: display limit],ERROR_TEST
  [] s=114 -> 1.0:(s'=66);
  // PROGRESS_PATCH,REPEATED_PATCH
  [] s=115 -> 1.0:(s'=97);
  // python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity] 2>&1 | tail -[COUNT: display limit],ERROR_TEST
  [] s=116 -> 1.0:(s'=117);
  // python -m django test [MODULE: test module] --settings=[SETTINGS: settings module] -v [COUNT: verbosity] 2>&1 | tail -[COUNT: display limit],ERROR_TEST
  [] s=117 -> 1.0:(s'=118);
  // find [PATH: repository root] -name [FILE: test runner] -o -name [FILE: setup file] | head -[COUNT: display limit],DISCOVERY_TEST
  [] s=118 -> 1.0:(s'=119);
  // python [PATH: test runner] [MODULE: test module] -v [COUNT: verbosity] 2>&1 | tail -[COUNT: display limit],PROGRESS_TEST
  [] s=119 -> 1.0:(s'=77);
endmodule

label "success" = s=1 | s=65 | s=77;
label "fail" = false;
label "end" = s=1 | s=65 | s=77;

rewards "steps"
  true : 1;
endrewards
