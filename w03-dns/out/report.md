# 과제 2 보고서

## A. Wireshark 분석

- 위임 응답: 2번 패킷
- 1번 질의와 2번 응답의 transaction ID: `0x12ab`
- 최종 A record 응답: 6번 패킷
- 가장 큰 DNS 응답: 2번 패킷, 394 bytes
- 2번 패킷에는 여러 NS record와 glue address가 함께 들어 있어 가장 컸다.

## B. CDN과 DNS steering

분류 규칙은 최종 CNAME의 zone이 원래 사이트의 zone과 다르면 third-party로 판단하는 것이다.

| 사이트 | CNAME chain 길이 | 최종 zone | 실제 제3자(third-party) 여부 | 규칙의 판단 |
|---|---:|---|---|---|
| www.microsoft.com | 2 | akamaiedge.net | 예 | third-party, 정답 |
| www.netflix.com | 1 | netflix.com | 아니요 | first-party, 정답 |
| www.adobe.com | 2 | akamai.net | 예 | third-party, 정답 |
| www.cnn.com | 1 | fastly.net | 예 | third-party, 정답 |
| www.apple.com | 3 | akamaiedge.net | 예 | third-party, 정답 |
| www.korea.ac.kr | 0 | korea.ac.kr | 아니요 | first-party, 정답 |
| www.stanford.edu | 1 | netlifyglobalcdn.com | 예 | third-party, 정답 |
| www.bbc.co.uk | 2 | fastly.net | 예 | third-party, 정답 |
| www.spotify.com | 1 | fastly.net | 예 | third-party, 정답 |
| www.github.com | 1 | github.com | 아니요 | first-party, 정답 |
| www.wikipedia.org | 1 | wikimedia.org | 아니요 | third-party, 오답 |
| www.nytimes.com | 3 | fastly.net | 예 | third-party, 정답 |

## DNS steering 결과

CDN을 사용한 사이트 10개 중 7개가 DNS resolver 또는 접속 네트워크에 따라 서로 다른 주소 집합을 반환했다. 비교에 사용한 네트워크는 집 Wi-Fi와 휴대폰 핫스팟이었다.

## 분류 규칙의 한계

단순 zone 비교 규칙은 `www.wikipedia.org`를 잘못 분류했다. CNAME의 끝은 `dyna.wikimedia.org`여서 도메인 이름은 다르지만, Wikipedia와 Wikimedia는 서로 무관한 third-party CDN이 아니라 같은 운영 주체에 속한다. 따라서 이름만 비교해서는 실제 소유 관계를 정확히 판단할 수 없다.
