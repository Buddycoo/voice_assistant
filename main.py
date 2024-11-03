from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}


# Define a Pydantic model to handle incoming Dialogflow webhook requests
# class DialogflowRequest(BaseModel):
#     queryResult: Dict[str, Any]
#     session: str
#
#
# # Function to handle "order.add" intent
def handle_order_add(parameters: dict, session_id: str):
    food_items = parameters["food-item"]
    quantities = parameters['number']



    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry but can you provide the quantity of the food"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict
        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have ordered{order_str}"

    return JSONResponse(content={
        'fulfillmentText': fulfillment_text
    })






# # Function to handle "order.remove" intent
def handle_order_remove(parameters: Dict[str, Any], session_id: str):
    # Process the order removal based on parameters
    # For example: parameters can contain items to remove
    items = parameters.get("items", [])
    response_text = f"Removing {', '.join(items)} from your order."
    return {"fulfillmentText": response_text}


def track_order(parameters: dict, session_id: str):
    order_id = parameters['number']
    order_status = db_helper.get_order_status(order_id)
    if order_status is not None:
        fulfillment_text = f"The order status for order id: {int(order_id)} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {int(order_id)}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
@app.post("/")
async def webhook_handler(request: Request):
    # Parse the incoming request body
    dialogflow_req = await request.json()
    intent = dialogflow_req["queryResult"]["intent"]["displayName"]
    parameters = dialogflow_req['queryResult']['parameters']

    # Extract session ID from outputContexts in the request
    output_contexts = dialogflow_req['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    # Route the request based on intent
    intent_order_dict = {
        "track.order-context: ongoing-tracking": track_order,
        'order.add-context: ongoing-order': handle_order_add,
        # "order.complete-context: ongoing-order": complete_order,
        "order.remove-context: ongoing-order": handle_order_remove,
    }

    return  intent_order_dict[intent](parameters, session_id)
