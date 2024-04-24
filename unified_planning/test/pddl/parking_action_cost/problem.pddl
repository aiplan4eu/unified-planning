(define   (problem parking)
  (:domain parking)
  (:objects
     car_00  car_01 - car
     curb_00 curb_01 curb_02 curb_03 - curb
  )
  (:init
    (at-curb-num car_00 curb_00)
    (at-curb-num car_01 curb_01)
    (curb-clear curb_02)
    (curb-clear curb_03)
    (car-clear car_00)
    (car-clear car_01)
  (= (total-cost) 0)
  )
  (:goal
    (and
      (at-curb-num car_00 curb_02)
      (at-curb-num car_01 curb_03)
    )
  )
(:metric minimize (total-cost))
)
