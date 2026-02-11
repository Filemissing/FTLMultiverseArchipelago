---@diagnostic disable: lowercase-global
---@diagnostic disable: undefined-global
-- variables from hyperspace lua api
Hyperspace = Hyperspace
script = script
log = log
Defines = Defines
---@diagnostic enable: undefined-global

function OnLoad()
    -- initialize other variables
    clientToMod_vector = Hyperspace.vector_int(vectorSize)
    clientToMod_readIndex = -1

    modToClient_vector = Hyperspace.vector_int(vectorSize)
    modToClient_freeSpace = vectorSize - vectorMetaDataSize
    modToClient_queue = {}
    modToClient_writeIndex = -1
    modToClient_readIndex = -1

    clientToMod_vector[0] = -1  -- lastWriteIndex clientToMod_vector
    clientToMod_vector[1] = -1  -- lastReadIndex modToClient_vector
    modToClient_vector[0] = -1  -- lastWriteIndex modToClient_vector
    modToClient_vector[1] = -1  -- lastReadIndex clientToMod_vector

    Log("clientToMod Vector - " .. tostring(clientToMod_vector))
    Log("modToClient Vector - " .. tostring(modToClient_vector))

    Log("Loaded successfully")
end
function OnInit(newGame)
    if (newGame) then
        SendMessage("Started a new game")
    else
        SendMessage("Loaded previous save")
    end
end
function OnTick()
    CheckMessages()
    RemoveOldMessages()
end

-- handles all events that create a choicebox
function OnPostCreateChoiceBox(choiceBox, event)
    SendMessage(event.eventName)
end

function HandleMessage(id, msg)
    if(id <= clientToMod_readIndex)then
        return -- message has already been processed
    end
    Log("Recieved Message: "..id.."|"..msg)
    clientToMod_readIndex = id -- update readIndex (assumes ascending order handling)
    UpdateReadIndex(modToClient_vector, clientToMod_readIndex)
end

-- communication methods
function CheckMessages()
    messages = SplitMessages(clientToMod_vector)
    for _, msg in ipairs(messages) do
        str = Decode(msg.data)
        HandleMessage(msg.id, str)
    end
end
function SendMessage(message)
    if AppendMessage(message) then
        -- if the message was sent successfully
    else
        Log("Message queued: " .. message)
    end
    -- place to add aditional sending logic such as queue handling
end
function RemoveOldMessages()
    if clientToMod_vector[1] > modToClient_readIndex then -- if the readIndex increased
        for i = modToClient_readIndex + 1, clientToMod_vector[1] do
            RemoveMessage(modToClient_vector, i) -- remove all indexes between
        end
        modToClient_readIndex = clientToMod_vector[1] -- update the readIndex
    end
end
-- helper functions
function Log(msg)
    log(prefix .. msg)
end

function Encode(str)
    result = {}
    for i = 1, #str do
        table.insert(result, string.byte(str, i))
    end
    return result
end
function Decode(data)
    local chars = {}
    for _, v in ipairs(data) do
        if v == 0 then break end -- stop at null characters
        table.insert(chars, string.char(v))
    end
    return table.concat(chars)
end

-- clears all message data from the vector
function ClearMessages(vec)
    for i = vectorMetaDataSize, vec:size() - 1 do
        vec[i] = 0
    end
end
-- Writes all messages back-to-back into the vector
function WriteMessages(vec, messages)
    local writeIndex = vectorMetaDataSize
    for _, msg in ipairs(messages) do
        vec[writeIndex] = msg.id
        vec[writeIndex + 1] = #msg.data
        for k, byte in ipairs(msg.data) do
            vec[writeIndex + 1 + k] = byte
        end
        writeIndex = writeIndex + 2 + #msg.data
    end
end

-- generates a message with it's metaData
function GenerateMessage(message)
    local messageBodyData = Encode(message) -- flat byte array
    local result = { modToClient_writeIndex, #messageBodyData }
    for _, byte in ipairs(messageBodyData) do
        table.insert(result, byte)
    end
    return result
end

-- appends a message to the end of the vector
function AppendMessage(message)
    if modToClient_freeSpace < #message + messageMetaDataSize then
        -- if the message is too long queue it, hopefully never happens, might need to store persistently if we need to be extra safe 
        table.insert(modToClient_queue, message)
        Log("Added message to the queue (time to actually implement it...)")
        return false
    end

    modToClient_writeIndex = modToClient_writeIndex + 1 -- increment write index

    messageData = GenerateMessage(message)

    startIndex = vectorSize - modToClient_freeSpace

    for offset = 0, #messageData - 1 do
        modToClient_vector[startIndex + offset] = messageData[offset + 1]
    end

    modToClient_freeSpace = modToClient_freeSpace - #messageData

    modToClient_vector[0] = modToClient_writeIndex -- update writeIndex in vector

    return true
end

-- reads a vector and splits it into all messages, returns an ordered table of those messages containing {id, data}
function SplitMessages(vec)
    local messages = {}
    local i = vectorMetaDataSize
    while i < vec:size() do
        local id = vec[i]
        local length = vec[i + 1]
        if id == nil or length == nil or length == 0 then
            break -- no more messages
        end

        local data = {}
        for j = i + 2, i + 2 + length - 1 do
            table.insert(data, vec[j])
        end

        table.insert(messages, {id = id, data = data})
        i = i + 2 + length
    end
    return messages
end

-- Removes one message by ID and rewrites vector
function RemoveMessage(vec, removeId)
    local allMessages = SplitMessages(vec)

    -- Filter out the target
    local filtered = {}
    local removed = {}
    for _, msg in ipairs(allMessages) do
        if msg.id ~= removeId then
            table.insert(filtered, msg)
        else
            table.insert(removed, msg)
        end
    end

    for _, msg in ipairs(removed) do
        modToClient_freeSpace = modToClient_freeSpace + #msg.data + 2
    end

    -- Rewrite
    ClearMessages(vec)
    WriteMessages(vec, filtered)
end

function UpdateReadIndex(vec, readIndex)
    vec[1] = readIndex
end
function UpdateWriteIndex(vec, writeIndex)
    vec[0] = writeIndex
    
end

-- static variables
prefix = "[FTLArchipelago] "
vectorSize = 4096
vectorMetaDataSize = 2 -- last written index of that vector, last read index for the opposing vector
messageMetaDataSize = 2 -- index of the message, length of the message body

-- resgister functions
script.on_load(OnLoad)
script.on_init(OnInit)
script.on_internal_event(Defines.InternalEvents.ON_TICK, OnTick)
script.on_internal_event(Defines.InternalEvents.POST_CREATE_CHOICEBOX, OnPostCreateChoiceBox)