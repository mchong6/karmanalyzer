#!/usr/bin/env th
require 'xlua'
require 'optim'
require 'nn'
require 'image'
require 'cunn'
require 'gnuplot'
--dofile './provider.lua'
local Provider = torch.class 'Provider'

torch.setdefaulttensortype('torch.FloatTensor')
torch.manualSeed(300)

opt = lapp[[
   -b,--batchSize             (default 10)          batch size
   -r,--learningRate          (default 1e-5)        learning rate
   --learningRateDecay        (default 1.0e-7)      learning rate decay
   --weightDecay              (default 0.0005)      weightDecay
   -m,--momentum              (default 0.9)         momentum
   --epoch_step               (default 25)          epoch step
   --max_epoch                (default 100)           maximum number of iterations
]]
print(opt)

--load dataset from t7 file
dataset = torch.load 'data.t7'
--split dataset
train_images = dataset.trainData.data:cuda()
train_features = dataset.trainData.data_feature:cuda()
train_labels = dataset.trainData.labels:cuda()
--for graphing
local accuracy = nil

-----------------model-----------------------

local vgg = nn.Sequential()
-- building block
local function ConvBNReLU(nInputPlane, nOutputPlane)
  vgg:add(nn.SpatialConvolution(nInputPlane, nOutputPlane, 3,3, 1,1, 1,1))
  --vgg:add(nn.SpatialBatchNormalization(nOutputPlane,1e-3))
  vgg:add(nn.ReLU(true))
  return vgg
end
-- Will use "ceil" MaxPooling because we want to save as much feature space as we can
local MaxPooling = nn.SpatialMaxPooling

ConvBNReLU(3,32):add(nn.Dropout(0.3))
ConvBNReLU(32,64)
vgg:add(MaxPooling(2,2,2,2):ceil())
ConvBNReLU(64,128):add(nn.Dropout(0.4))
vgg:add(MaxPooling(2,2,2,2):ceil())
ConvBNReLU(128,256):add(nn.Dropout(0.4))
vgg:add(MaxPooling(2,2,2,2):ceil())
--print(#vgg:cuda():forward(torch.CudaTensor(5,3,32,32)))


vgg:add(nn.View(256*4*4))
vgg:add(nn.Linear(256*4*4, 10000))
vgg:add(nn.ReLU(true))
vgg:add(nn.Linear(10000, 1))
vgg:add(nn.ReLU(true))


--[[local combination = nn.Sequential()
combination:add(nn.Linear(10, 1000))
combination:add(nn.ReLU(true))
combination:add(nn.Linear(1000, 4000))
combination:add(nn.ReLU(true))
combination:add(nn.Linear(4000, 1000))
combination:add(nn.ReLU(true))
combination:add(nn.Linear(1000, 1))
combination:add(nn.ReLU(true))]]

--[[local pl = nn.ParallelTable()
pl:add(vgg)
pl:add(nn.Identity())]]

local model = nn.Sequential()
--model:add(pl)
--model:add(nn.JoinTable(2))
model:add(vgg)
--model:add(combination)


print(model)
model = model:cuda()
----------------------------------------

parameters,gradParameters = model:getParameters()
criterion = nn.MSECriterion():cuda()

optimState = {
    learningRate = opt.learningRate,
    weightDecay = opt.weightDecay,
    momentum = opt.momentum,
    learningRateDecay = opt.learningRateDecay,
}
--confusion = optim.ConfusionMatrix(10)


function train()
	model:training()
	epoch = epoch or 1

	-- drop learning rate every "epoch_step" epochs
	if epoch % opt.epoch_step == 0 then optimState.learningRate = optimState.learningRate/2
	end

	print('==>'.." online epoch # " .. epoch .. ' [batchSize = ' .. opt.batchSize .. ']')
	--randomly break training data into batches
	local indices = torch.randperm(train_images:size(1)):long():split(opt.batchSize)
	-- remove last element so that all the batches have equal size
	indices[#indices] = nil

	local tic = torch.tic()
	local err = 0
	for t,v in ipairs(indices) do
		xlua.progress(t, #indices)
		local inputs = train_images:index(1,v):cuda()
        local inputs_feature = train_features:index(1,v):cuda()
		local targets = train_labels:index(1,v):cuda()
		local feval = function(x)
			if x ~= parameters then parameters:copy(x) end
			gradParameters:zero()    
			--local outputs = model:forward({inputs, inputs_feature})
			local outputs = model:forward(inputs)
			local f = criterion:forward(outputs, targets)
			err = err + f
			local df_do = criterion:backward(outputs, targets)
			--model:backward({inputs, inputs_feature}, df_do)			
			model:backward(inputs, df_do)			
            --confusion:batchAdd(outputs, targets)
			return f ,gradParameters
		end
		optim.sgd(feval, parameters, optimState)
	end
	print('Total Error: '..  err/train_images:size(1))
	epoch = epoch + 1
end

function test()
	model:evaluate()	
    local correct = 0
    model:evaluate()
    print('==>'.." testing")
    local predict = model:forward(test_images)
    confusion:batchAdd(predict, test_labels)
    confusion:updateValids()
    print(tostring(confusion))
    --[[
	--get index of the maximum output
    local value, index = predict:max(2) 
    for i = 1, predict:size(1) do
        local prediction = index[i][1]
        --index 10 is for 0
        if prediction == 10 then
            prediction = 0
        end
        if prediction == test_labels[i] then
            correct = correct + 1
        elseif epoch == 50 then
            image.save('./wrong/wrong_pic'..'_'..test_labels[i]..'_'..prediction..'.jpg', test_images[i])
        end
    end]]
    print('Accuracy: ', confusion.totalValid*100)
    --print('Test accuracy:', correct / 1000)
	if accuracy == nil then
		accuracy = torch.CudaTensor(1):fill(tonumber(confusion.totalValid*100))
	else
		accuracy = accuracy:cat(torch.CudaTensor(1):fill(tostring(confusion.totalValid*100)))
	end
    confusion:zero()
end

for i=1, opt.max_epoch do
    train()
    --test()
	--save graph every 50 epoch
	if i % 10 == 0 then
		torch.save('model.net', model)
	end
end
--plot graph
gnuplot.pngfigure('./accuracy.png')
gnuplot.plot('accuracy', accuracy, '-')
gnuplot.xlabel('Epoch')
gnuplot.ylabel('Accuracy')
gnuplot.plotflush()
