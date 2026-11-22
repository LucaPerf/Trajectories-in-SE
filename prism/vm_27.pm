dtmc

module chain
  s : [0..77] init 0;
  // init
  [] s=0 -> 0.030927835051546393:(s'=1) + 0.030927835051546393:(s'=2) + 0.030927835051546393:(s'=3) + 0.030927835051546393:(s'=4) + 0.09278350515463918:(s'=5) + 0.030927835051546393:(s'=6) + 0.030927835051546393:(s'=7) + 0.030927835051546393:(s'=8) + 0.030927835051546393:(s'=9) + 0.030927835051546393:(s'=10) + 0.061855670103092786:(s'=11) + 0.12371134020618557:(s'=12) + 0.3195876288659794:(s'=13) + 0.030927835051546393:(s'=14) + 0.09278350515463918:(s'=15);
  // cat [FILE: choices file],DISCOVERY_SOURCE
  [] s=1 -> 0.34313725490196073:(s'=16) + 0.2647058823529412:(s'=29) + 0.0392156862745098:(s'=30) + 0.0392156862745098:(s'=39) + 0.0784313725490196:(s'=42) + 0.0392156862745098:(s'=43) + 0.0392156862745098:(s'=45) + 0.0784313725490196:(s'=46) + 0.0392156862745098:(s'=50) + 0.0392156862745098:(s'=58);
  // cat [FILE: choices file],ERROR_SOURCE
  [] s=2 -> 0.2:(s'=3) + 0.2:(s'=4) + 0.2:(s'=17) + 0.2:(s'=24) + 0.2:(s'=27);
  // find [PATH: repository root] -name [GLOB: Python files] | xargs grep -l [PATTERN: choices class] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=3 -> 1.0:(s'=1);
  // find [PATH: repository root] -type f -name [GLOB: Python files] -exec grep -l [PATTERN: choices class] [EXEC: find replacement] \;,DISCOVERY_SOURCE
  [] s=4 -> 0.5:(s'=1) + 0.5:(s'=33);
  // find [PATH: repository root] -type f -name [GLOB: Python files] | head [COUNT: line limit],DISCOVERY_REPO
  [] s=5 -> 0.33333333333333337:(s'=1) + 0.33333333333333337:(s'=18) + 0.33333333333333337:(s'=19);
  // find [PATH: repository root] -type f -name [GLOB: Python files] | head [COUNT: line limit],DISCOVERY_TEST
  [] s=6 -> 1.0:(s'=8);
  // find [PATH: repository root] -type f -name [GLOB: Python files] | head [COUNT: line limit],INFO_REPO
  [] s=7 -> 1.0:(s'=20);
  // grep -r [PATTERN: choices class] [PATH: repository root] --include [GLOB: Python files],DISCOVERY_SOURCE
  [] s=8 -> 0.33333333333333337:(s'=1) + 0.33333333333333337:(s'=22) + 0.33333333333333337:(s'=32);
  // grep -rn [PATTERN: choices class] [PATH: repository root] --include [GLOB: Python files],DISCOVERY_SOURCE
  [] s=9 -> 1.0:(s'=1);
  // grep -rn [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files],DISCOVERY_SOURCE
  [] s=10 -> 1.0:(s'=1);
  // ls -la [PATH: repository root],DISCOVERY_REPO
  [] s=11 -> 1.0:(s'=2);
  // ls -la [PATH: repository root],INFO_REPO
  [] s=12 -> 0.25:(s'=2) + 0.25:(s'=3) + 0.5:(s'=21);
  // ls [PATH: repository root],DISCOVERY_REPO
  [] s=13 -> 0.1:(s'=1) + 0.1:(s'=2) + 0.1:(s'=3) + 0.1:(s'=20) + 0.2:(s'=21) + 0.1:(s'=22) + 0.1:(s'=23) + 0.1:(s'=24) + 0.1:(s'=25);
  // ls [PATH: repository root],ERROR_NONE
  [] s=14 -> 1.0:(s'=8);
  // ls [PATH: repository root],INFO_REPO
  [] s=15 -> 0.33333333333333337:(s'=23) + 0.33333333333333337:(s'=26) + 0.33333333333333337:(s'=27);
  // python3 << [SCRIPT: patch choices file],PROGRESS_PATCH
  [] s=16 -> 0.17346938775510207:(s'=16) + 0.30612244897959184:(s'=28) + 0.04081632653061225:(s'=29) + 0.35714285714285715:(s'=41) + 0.04081632653061225:(s'=53) + 0.04081632653061225:(s'=56) + 0.04081632653061225:(s'=77);
  // find [PATH: repository root] -name [GLOB: filename] -type f,EMPTY_SOURCE
  [] s=17 -> 1.0:(s'=21);
  // find [PATH: repository root] -name [GLOB: filename] -path [GLOB: source package path] | head [COUNT: line limit],EMPTY_SOURCE
  [] s=18 -> 0.5:(s'=18) + 0.5:(s'=37);
  // grep -rn [PATTERN: choices class] [FILE: source file] | head [COUNT: line limit],EMPTY_SOURCE
  [] s=19 -> 1.0:(s'=31);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files] -l,DISCOVERY_SOURCE
  [] s=20 -> 0.5:(s'=1) + 0.5:(s'=22);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files],DISCOVERY_SOURCE
  [] s=21 -> 0.6:(s'=1) + 0.2:(s'=22) + 0.2:(s'=33);
  // cat [FILE: source file],DISCOVERY_SOURCE
  [] s=22 -> 0.25:(s'=16) + 0.5:(s'=29) + 0.25:(s'=34);
  // cat [FILE: source file],ERROR_SOURCE
  [] s=23 -> 0.5:(s'=1) + 0.5:(s'=35);
  // find [PATH: source package] -name [GLOB: Python files] -exec grep -l [PATTERN: choices class] [EXEC: find replacement] \;,DISCOVERY_SOURCE
  [] s=24 -> 1.0:(s'=1);
  // grep -r [PATTERN: choices class] [PATH: source package],ERROR_SOURCE
  [] s=25 -> 1.0:(s'=1);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files],ERROR_SOURCE
  [] s=26 -> 1.0:(s'=1);
  // grep -r [PATTERN: choices class] [PATH: source package],DISCOVERY_SOURCE
  [] s=27 -> 1.0:(s'=1);
  // submit_patch,PROGRESS_TEST__success
  [] s=28 -> 1.0:(s'=28);
  // cat > [FILE: choices file] << [SCRIPT: patch choices file],PROGRESS_PATCH
  [] s=29 -> 0.38:(s'=28) + 0.28:(s'=29) + 0.03:(s'=40) + 0.22:(s'=41) + 0.06:(s'=53) + 0.03:(s'=67);
  // find [PATH: repository root] -type f -name [GLOB: Python files] -path [GLOB: test path] -exec grep -l [PATTERN: choices class] [EXEC: find replacement] \; | head [COUNT: line limit],DISCOVERY_TEST
  [] s=30 -> 1.0:(s'=36);
  // grep -rn [PATTERN: choices class] [PATH: source package] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=31 -> 1.0:(s'=1);
  // grep -n [PATTERN: code symbols] [FILE: source file] | head [COUNT: line limit],EMPTY_SOURCE
  [] s=32 -> 1.0:(s'=38);
  // cat [FILE: choices file],ERROR_NONE
  [] s=33 -> 1.0:(s'=1);
  // python3 -c [SCRIPT: patch choices file],PROGRESS_PATCH
  [] s=34 -> 0.5:(s'=29) + 0.5:(s'=41);
  // find [PATH: repository root] -name [GLOB: filename] -type f,DISCOVERY_SOURCE
  [] s=35 -> 1.0:(s'=44);
  // grep -rn [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files],EMPTY_SOURCE
  [] s=36 -> 1.0:(s'=29);
  // find [PATH: repository root] -name [GLOB: filename] | head [COUNT: line limit],EMPTY_SOURCE
  [] s=37 -> 1.0:(s'=47);
  // cat [FILE: choices file],INFO_SOURCE
  [] s=38 -> 1.0:(s'=48);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files] -A [COUNT: context],DISCOVERY_SOURCE
  [] s=39 -> 1.0:(s'=49);
  // submit_patch,PROGRESS_PATCH__success
  [] s=40 -> 1.0:(s'=40);
  // cat [FILE: choices file],REPEATED_SOURCE
  [] s=41 -> 0.09615384615384616:(s'=16) + 0.19230769230769232:(s'=28) + 0.14423076923076922:(s'=29) + 0.04807692307692308:(s'=40) + 0.24038461538461536:(s'=41) + 0.028846153846153844:(s'=43) + 0.028846153846153844:(s'=53) + 0.04807692307692308:(s'=54) + 0.028846153846153844:(s'=55) + 0.028846153846153844:(s'=57) + 0.028846153846153844:(s'=60) + 0.028846153846153844:(s'=68) + 0.028846153846153844:(s'=70) + 0.028846153846153844:(s'=74);
  // cat [FILE: choices file] | head [COUNT: line limit],REPEATED_SOURCE
  [] s=42 -> 1.0:(s'=41);
  // sed -i [SCRIPT: patch choices file] [FILE: choices file],PROGRESS_PATCH
  [] s=43 -> 0.33:(s'=34) + 0.67:(s'=41);
  // sed -n [RANGE: line range] [FILE: source file],DISCOVERY_SOURCE
  [] s=44 -> 1.0:(s'=51);
  // python3 << [SCRIPT: patch choices file],ERROR_SOURCE
  [] s=45 -> 1.0:(s'=16);
  // cat > [FILE: patch script] << [SCRIPT: patch choices file] ; python3 [FILE: patch script],PROGRESS_PATCH
  [] s=46 -> 0.33:(s'=29) + 0.67:(s'=41);
  // find [PATH: repository root] -path [GLOB: source package path] -name [GLOB: Python files] | grep -i [PATTERN: code symbols],DISCOVERY_SOURCE
  [] s=47 -> 1.0:(s'=1);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files] -l,DISCOVERY_TEST
  [] s=48 -> 1.0:(s'=52);
  // grep -r [PATTERN: code symbols] [FILE: source file] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=49 -> 0.5:(s'=49) + 0.5:(s'=59);
  // cat [FILE: source file] | head [COUNT: line limit],INFO_SOURCE
  [] s=50 -> 1.0:(s'=55);
  // cat > [FILE: patch script] << [SCRIPT: patch choices file] ; python [FILE: patch script],PROGRESS_PATCH
  [] s=51 -> 0.5:(s'=53) + 0.5:(s'=62);
  // grep -n [PATTERN: code symbols] [FILE: source file] | head [COUNT: line limit],INFO_SOURCE
  [] s=52 -> 0.29:(s'=41) + 0.29:(s'=52) + 0.14:(s'=64) + 0.14:(s'=66) + 0.14:(s'=70);
  // submit_patch,ERROR_TEST
  [] s=53 -> 0.2:(s'=16) + 0.4:(s'=29) + 0.2:(s'=43) + 0.2:(s'=51);
  // cat [FILE: choices file] | tail [COUNT: line limit],DISCOVERY_SOURCE
  [] s=54 -> 0.5:(s'=41) + 0.5:(s'=73);
  // grep -n [PATTERN: code symbols] [FILE: source file],EMPTY_SOURCE
  [] s=55 -> 1.0:(s'=16);
  // grep -r [PATTERN: choices class] [PATH: source package] --include [GLOB: Python files],REPEATED_SOURCE
  [] s=56 -> 1.0:(s'=41);
  // cat [FILE: choices test],DISCOVERY_TEST
  [] s=57 -> 1.0:(s'=61);
  // grep -n [PATTERN: code symbols] [FILE: source file] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=58 -> 1.0:(s'=46);
  // grep -r [PATTERN: code symbols] [FILE: source file] -A [COUNT: context] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=59 -> 0.5:(s'=59) + 0.5:(s'=65);
  // python3 -c [SCRIPT: inline test],PROGRESS_TEST
  [] s=60 -> 0.5:(s'=16) + 0.5:(s'=28);
  // grep -rn [PATTERN: dunder methods] [FILE: choices file],EMPTY_SOURCE
  [] s=61 -> 1.0:(s'=63);
  // cd [PATH: repository root] && python [FILE: test runner] [TEST: test module],PROGRESS_TEST
  [] s=62 -> 1.0:(s'=41);
  // cat [FILE: choices test] | head [COUNT: line limit],REPEATED_TEST
  [] s=63 -> 1.0:(s'=28);
  // grep -n [PATTERN: code symbols] [FILE: source file] | grep -A [COUNT: context] -B [COUNT: context] [PATTERN: line numbers] | head [COUNT: line limit],EMPTY_SOURCE
  [] s=64 -> 0.5:(s'=41) + 0.5:(s'=52);
  // grep -r [PATTERN: code symbols] [FILE: source file] -A [COUNT: context] | grep -A [COUNT: context] [PATTERN: class name] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=65 -> 1.0:(s'=52);
  // grep -n [PATTERN: code symbols] [FILE: source file] | grep -A [COUNT: context] -B [COUNT: context] [PATTERN: line numbers] | head [COUNT: line limit],INFO_SOURCE
  [] s=66 -> 1.0:(s'=64);
  // cat [FILE: choices test] | head [COUNT: line limit],DISCOVERY_TEST
  [] s=67 -> 1.0:(s'=29);
  // python3 -c [SCRIPT: inline test],ERROR_TEST
  [] s=68 -> 1.0:(s'=69);
  // grep -n [PATTERN: code symbols] [FILE: source file],INFO_SOURCE
  [] s=69 -> 0.5:(s'=70) + 0.5:(s'=71);
  // grep -n [PATTERN: code symbols] [FILE: source file] -A [COUNT: context] | head [COUNT: line limit],INFO_SOURCE
  [] s=70 -> 0.25:(s'=69) + 0.25:(s'=70) + 0.25:(s'=72) + 0.25:(s'=75);
  // grep -n [PATTERN: choices class] [FILE: choices file] -A [COUNT: context],ERROR_SOURCE
  [] s=71 -> 1.0:(s'=52);
  // grep -n [PATTERN: code symbols] [FILE: source file] -A [COUNT: context] | grep -A [COUNT: context] [PATTERN: line numbers],ERROR_NONE
  [] s=72 -> 1.0:(s'=52);
  // cat [FILE: choices file] | tail [COUNT: line limit],REPEATED_SOURCE
  [] s=73 -> 1.0:(s'=29);
  // grep -n [PATTERN: code symbols] [FILE: source file] -A [COUNT: context] | grep -A [COUNT: context] [PATTERN: line numbers],INFO_SOURCE
  [] s=74 -> 0.5:(s'=41) + 0.5:(s'=74);
  // sed -n [RANGE: line range] [FILE: source file],INFO_SOURCE
  [] s=75 -> 0.33333333333333337:(s'=60) + 0.33333333333333337:(s'=75) + 0.33333333333333337:(s'=76);
  // grep -n [PATTERN: dunder methods] [FILE: choices file],ERROR_NONE
  [] s=76 -> 1.0:(s'=75);
  // sed -n [RANGE: line range] [FILE: source file],PROGRESS_PATCH
  [] s=77 -> 1.0:(s'=41);
endmodule

label "success" = s=28 | s=40;
label "fail" = false;
label "end" = s=28 | s=40;

rewards "steps"
  true : 1;
endrewards
