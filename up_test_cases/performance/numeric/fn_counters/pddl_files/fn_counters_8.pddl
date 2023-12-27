;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
(define (problem instance_8)
  (:domain fn-counters)
  (:objects
    c0 c1 c2 c3 c4 c5 c6 c7 - counter
  )

  (:init
    (= (max_int) 16)
	(= (value c0) 0)
	(= (value c1) 0)
	(= (value c2) 0)
	(= (value c3) 0)
	(= (value c4) 0)
	(= (value c5) 0)
	(= (value c6) 0)
	(= (value c7) 0)
  )

  (:goal (and 
    (<= (+ (value c0) 1) (value c1))
	(<= (+ (value c1) 1) (value c2))
	(<= (+ (value c2) 1) (value c3))
	(<= (+ (value c3) 1) (value c4))
	(<= (+ (value c4) 1) (value c5))
	(<= (+ (value c5) 1) (value c6))
	(<= (+ (value c6) 1) (value c7))
  ))

  
)
