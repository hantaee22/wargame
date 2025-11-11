const words = require("./ag")                  // 외부 파일 "ag.js"에서 데이터(words)를 불러옴
const express = require("express")             // Express 웹 프레임워크 불러오기

const PORT = 3000                              // 서버 실행 포트 번호
const app = express()                          // Express 앱 객체 생성
app.set('case sensitive routing', true)        // 라우팅에서 대소문자를 구분하도록 설정
app.use(express.urlencoded({ extended: true }))// POST 요청의 body 데이터를 urlencoded 형식으로 파싱

// 단어 검색 함수: words 배열에서 name 속성이 요청값과 일치하는 객체를 반환
function search(words, leg) {
    return words.find(word => word.name === leg.toUpperCase())
}

// GET / : 기본 라우트, 단순 인사말 반환
app.get("/",(req, res)=>{
    return res.send("hi guest")
})

// POST /shop : 입력된 leg 값에 따라 동작
app.post("/shop",(req, res)=>{
    const leg = req.body.leg.toLowerCase()     // 클라이언트에서 전달된 leg 값을 소문자로 변환

    if (leg == 'flag'){                        // 만약 'flag' 요청이면 차단
        return res.status(403).send("Access Denied")
    }

    const obj = search(words,leg)              // words 배열에서 일치하는 객체 검색

    if (obj){                                  // 객체가 존재하면 JSON 형식으로 응답
        return res.send(JSON.stringify(obj))
    }

    return res.status(404).send("Nothing")     // 없으면 404 에러 반환
})

// 서버 실행
app.listen(PORT,()=>{
    console.log(`[+] Started on ${PORT}`)
})
