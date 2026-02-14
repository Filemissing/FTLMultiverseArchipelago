this document describes how packets are sent through the memory channel

an important detail to note is that the client has the most information and is thus responsible for filtering any data received from the server or mod and sending only the correct data through to the other party
## mod -> client packets

| Structure                    | Purpose                                                      |
| ---------------------------- | ------------------------------------------------------------ |
| CHOICE\|<choice_id>          | sent for every encountered choicebox                         |
| LOCATION\|<ap_location_name> | sent for any other location, should use the AP location name |
| DEATH\|<optional_reason>     | sent for death link                                          |
| EXIT                         | sent on game quit                                            |

## client -> mod packets

| Structure                                   | Purpose                                       |
| ------------------------------------------- | --------------------------------------------- |
| ITEM\|<item_type>\|<item_id>\|<item_amount> | sent when the client recieves an item from AP |
| DEATH                                       | sent when recieving death link                |
| EXIT                                        | sent when the client shuts down               |

