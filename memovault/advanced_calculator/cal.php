<?php
error_reporting(0);                      // 모든 PHP 에러/경고 출력 끔 (디버깅/보안상 위험: 치명적 에러는 숨겨지지 않음)

$flag = file_get_contents('/flag');      // 컨테이너/서버 내 /flag 파일을 읽어 변수에 저장
putenv("FLAG=".$flag);                   // 환경변수 FLAG에 플래그 값을 저장 (PHP 상수 정의가 아님: getenv('FLAG')로 접근 가능)

// {placeholder} 의 형식을 매칭하기 위한 정규식 부품
//  - 첫 글자는 알파벳 [[:alpha:]]
//  - 이후에는 공백, >, }, <, `, {, ", ' 을 제외한 어떤 문자든 반복
const PLACEHOLDER_REGEX_PART = '[[:alpha:]][^>} <`{"\']*';
// 실제로 { ... } 전체를 매칭하는 정규식
const PLACEHOLDER_REGEX = '~\{(' . PLACEHOLDER_REGEX_PART . ')\}~';

$error=null;                             // 검사 결과 에러 메시지(없으면 null/false)
$result=null;                            // 계산 결과

// Moodle 코드 일부를 가져온 수식 검증 함수
function check_formula($formula) {
    // 1) 주석/태그 시작 토큰이 포함되면 즉시 차단
    foreach (['//', '/*', '#', '<?', '?>'] as $commentstart) {
        if (strpos($formula, $commentstart) !== false) {
            return 'no hack';            // 금지된 토큰 감지
        }
    }
    
    // 2) {placeholder} 들을 임시로 '1.0' 으로 치환 (검증을 수월하게 하기 위함)
    $formula = preg_replace(PLACEHOLDER_REGEX, '1.0', $formula); // 취약점 ->{ } 안에있는 토큰을 1.0으로 바꾸어줌
    // 3) 소문자화 + 공백 제거
    $formula = strtolower(str_replace(' ', '', $formula));
    
    // 4) 허용되는 연산자 집합과 숫자/연산자 패턴을 정의
    $safeoperatorchar = '-+/*%>:^\~<?=&|!';    // 허용 연산자 문자들
    $operatorornumber = "[{$safeoperatorchar}.0-9eE]"; // 연산자 또는 숫자(지수 표기 포함)

    // 5) 함수 호출 패턴을 반복적으로 찾아 검증/제거
    //    - 형태:  func(arg1, arg2, arg3, ...)
    //    - 인자들은 연산자/숫자/점/지수 문자로만 구성되어야 함
    while (preg_match("~(^|[{$safeoperatorchar},(])([a-z0-9_]*)".
             "\\(({$operatorornumber}+(,{$operatorornumber}+((,{$operatorornumber}+)+)?)?)?\\)~",
             $formula, $regs)) {

        switch ($regs[2]) {
            case '':
                // 함수명이 비어 있는데 인자가 있거나, 인자 길이가 0인 경우 -> 문법 오류
                if ((isset($regs[4]) && $regs[4]) || strlen($regs[3]) == 0) {
                    return $regs[0].' Illegal formula syntax';
                }
                break;
    
            case 'pi':
                // pi 는 인자 불필요
                if (array_key_exists(3, $regs)) {
                    return $regs[2].' does not require any args';
                }
                break;

            // 인자 1개 또는 2개 허용되는 함수 화이트리스트
            case 'abs': case 'ceil':
            case 'decbin': case 'decoct': case 'deg2rad':
            case 'exp': case 'floor':
            case 'octdec': case 'rad2deg':
            case 'round':
                // 3개 이상 인자 금지, 최소 1개는 있어야 함
                if (!empty($regs[5]) || empty($regs[3])) {
                    return $regs[2].' requires one or two args';
                }
                break;
    
            default:
                // 그 외 함수명은 미지원
                return $regs[2].' is not supported';
        }

        // 6) 검증을 통과한 해당 함수 호출 토큰을 '1.0'으로 치환하여 제거(안전화)
        if ($regs[1]) {
            // 함수 앞에 뭔가(연산자 등)가 있으면 그대로 유지 + 1.0로 대체
            $formula = str_replace($regs[0], $regs[1] . '1.0', $formula);
        } else {
            // 문자열 시작에서 함수가 나왔다면 그 전체를 1.0으로 대체
            $formula = preg_replace('~^' . preg_quote($regs[2], '~') . '\([^)]*\)~', '1.0', $formula);
        }
    }

    // 7) 남은 문자열에 허용되지 않은 문자(알파벳 등)가 남아있다면 불법 문법
    if (preg_match("~[^{$safeoperatorchar}.0-9eE]+~", $formula, $regs)) {
        return $regs[0].' Illegal formula syntax';
    } else {
        // 모든 검증 통과
        return false;
    }
}

function calculate($formula){
    global $error;
    // 사용자가 입력한 원본 수식을 검증
    $error = check_formula($formula);
    if($error){
        // 에러가 있으면 현재는 아무 것도 하지 않음 (에러 메시지는 전역 $error에 저장되어 있음)
    } else {
        // 변수 변수(variable variables) 방지 목적: 중괄호를 소괄호로 치환
        //  예: {x} -> (x)
        //  ※ 아래 평가는 '원본 수식'에 대해 이 치환만 적용 후 실행됨
        $formula = str_replace('{', '(', $formula);
        $formula = str_replace('}', ')', $formula);
        
        // eval로 계산: "return [수식];"
        //  ex) "1+2*(3-1)" -> eval("return 1+2*(3-1);")
        return eval('return ' . $formula . ';');
    }
}

if (isset($_GET['f']) && $_GET['f'] !== ''){
    // GET 파라미터 f로 수식을 입력받아 계산 수행
    $formula = $_GET['f'];
    $result = calculate($formula);
}
