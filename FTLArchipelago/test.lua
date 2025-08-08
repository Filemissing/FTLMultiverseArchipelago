---@diagnostic disable: lowercase-global
---@diagnostic disable: undefined-global
-- variables from hyperspace lua api
Hyperspace = Hyperspace
script = script
log = log
Defines = Defines
---@diagnostic enable: undefined-global

function Encode(str, vector)
    -- Reset vector to 0
    for i = 0, vector:size() - 1 do
        vector[i] = 0
    end
    -- Write the new string’s ASCII codes
    for i = 1, #str do
        vector[i - 1] = string.byte(str, i)
    end
end

function Decode(vector)
    local chars = {}
    for i = 0, vector:size() - 1 do
        local v = vector[i]
        if v == 0 then break end -- stop at null characters
        table.insert(chars, string.char(v))
    end
    return table.concat(chars)
end

-- Create two 1024-int shared memory vectors
clientToMod = Hyperspace.vector_int(1024)
modToClient = Hyperspace.vector_int(1024)

-- Write default messages
Encode("FTLArchipelago clientToMod channel", clientToMod)
Encode("FTLArchipelago modToClient channel", modToClient)

function OnLoad()
    log("FTLArchipelago: clientToMod Vector - " .. tostring(clientToMod))
    log("FTLArchipelago: modToClient Vector - " .. tostring(modToClient))

    log("FTLArchipelago: Loaded successfully")
end

function OnRunStart()
    Encode("Started new run", modToClient)
end

function OnTick()
    recievedMessage = CheckMessages()

    if recievedMessage == "recieved SCRAPx1000" then
        Hyperspace.ships.player:ModifyScrapCount(1000, false)
    end
end

lastMessage = Decode(clientToMod)
function CheckMessages()
    message = Decode(clientToMod)
    if  lastMessage == nil or lastMessage ~= message then
        log("[FTLArchipelago] recieved message: " .. message)
        lastMessage = message
        return message
    else
        return nil
    end
end

function OnGameEvent()
    
end


script.on_load(OnLoad)
script.on_init(OnRunStart)
script.on_internal_event(Defines.InternalEvents.ON_TICK, OnTick)
script.on_game_event("", false, OnGameEvent)