;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
(define
  (problem car_max_accel_3)
  (:domain car)

  (:init
    (= (d) 0)
    (= (v) 0)
    (engine_stopped)
    (= (a) 0)
    (= (max_acceleration) 10.0)
    (= (min_acceleration) -10.0)
  )

  (:goal ;; to reach distance 10
    (and (> (d) 29 ) (< (d) 32 ) (< (v) 0.5) (> (v) -0.5) (= (a) 0))
  )


)
