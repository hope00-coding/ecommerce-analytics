with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select
        order_id,
        sum(price)         as total_price,
        sum(freight_value) as total_freight,
        count(*)           as item_count
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments as (
    select
        order_id,
        sum(payment_value) as total_payment
    from {{ ref('stg_payments') }}
    group by order_id
),

reviews as (
    select
        order_id,
        review_score
    from {{ ref('stg_reviews') }}
),

final as (
    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.ordered_at,
        o.approved_at,
        o.shipped_at,
        o.delivered_at,
        o.estimated_delivery_at,
        i.total_price,
        i.total_freight,
        i.item_count,
        p.total_payment,
        r.review_score
    from orders o
    left join order_items i  on o.order_id = i.order_id
    left join payments p     on o.order_id = p.order_id
    left join reviews r      on o.order_id = r.order_id
)

select * from final