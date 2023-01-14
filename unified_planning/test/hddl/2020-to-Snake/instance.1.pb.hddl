(define (problem pb01)
  (:domain snake)

  (:objects
    viper - snake
    px0y0 px1y0 px2y0
    px0y1 px1y1 px2y1
    px0y2 px1y2 px2y2 - location
  )

  (:htn :subtasks (hunt))

  (:init
    (head viper px2y2)
    
    (tail viper px2y2)

    (mouse-at px0y0)

    (occupied px0y0)
    (occupied px2y2)

    (adjacent px0y0 px1y0) (adjacent px1y0 px0y0) (adjacent px1y0 px2y0) (adjacent px2y0 px1y0)
    (adjacent px0y1 px1y1) (adjacent px1y1 px0y1) (adjacent px1y1 px2y1) (adjacent px2y1 px1y1)
    (adjacent px0y2 px1y2) (adjacent px1y2 px0y2) (adjacent px1y2 px2y2) (adjacent px2y2 px1y2)

    (adjacent px0y0 px0y1) (adjacent px0y1 px0y0) (adjacent px1y0 px1y1) (adjacent px1y1 px1y0) (adjacent px2y0 px2y1) (adjacent px2y1 px2y0)
    (adjacent px0y1 px0y2) (adjacent px0y2 px0y1) (adjacent px1y1 px1y2) (adjacent px1y2 px1y1) (adjacent px2y1 px2y2) (adjacent px2y2 px2y1)
  )

)
