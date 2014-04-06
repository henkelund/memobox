(function (exports, ng, $, console) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	/* Repeat directive that activates tooltip  on loaded devices */
	box.directive('deviceRepeatDirective', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        scope.$emit('deviceRepeatDirective');
                        $(".device").tooltip();
                    });
                }
            }
        }
     });
	
	// Infinity constructor function to encapsulate HTTP and pagination logic
	box.factory('Infinity', function($http) {
	  var Infinity = function($scope) {
	  	this.me = $scope;
	    this.images = [];
	    this.busy = false;
	    this.after = 1;
	    this.viewMonth = null;
	    this.viewYear = null; 
		this.monthArr = "Alert";
		this.device = -1; 
		this.type = null; 
	};
	  
	  Infinity.prototype.showPicture = function(file) {
		$.ajax({
		    url : "/files/details?id="+file,
			async: false,
			context: this,
		    success : function(result){
				var ts = new Date(null);
				ts.setTime(result.created_at*1000);
				
				var time = new Date(result.created_at*1000);
				var viewMonth = time.getMonth();
				var viewYear = time.getFullYear().toString();
				var viewDate = time.getDate();
				var month = Array("January","February","March","April","May","June","July","August","September","October","November","December");
				
				$("#filesDetailModalLabel").html(result.name+" – "+viewDate +" "+ month[viewMonth] + ", "+viewYear+" – "+result.product_name);
				
				if(result.type == "video") {
					$("#moddalVideoContainer").html('<video id="modalVideo" style="display: none;" width="520" height="520" controls="controls" autoplay="autoplay"><source id="modalSource" src="" type="video/mp4" /></video>');
					$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/static/devices/")+"/"+result.name);
					$("#modalVideo").load();
					$("#modalVideo").show();
					$("#modalImage").hide();
				} else {
					$("#modalVideo").hide();
					$("#modalImage").show();
					$("#modalDownload").attr("href", "/files/stream/"+result._id+"/"+result.name);
					$("#modalImage").attr("src", "/static/images/"+result.thumbnail);
				}
		
		        $('#filesDetailModal').modal('show');				
		    }
		});	  	
  	
	  	//var f = new FileService();
	  	//f.loadDetails(file);	  	
	  }
	  
	  Infinity.prototype.nextPage = function(_device, _type) {
	    if (this.busy) return;
	    this.busy = true;	
	    
	    var changedState = false; 
		if(_device != null) {
			if(this.device != _device) {
				changedState = true;
				this.after = 1; 
				$(".device span").removeClass("selectedDevice");
				$("#"+_device+" span").addClass("selectedDevice");
				this.device = _device; 
			} else {
				this.device = -1; 
				$(".device span").removeClass("selectedDevice");
				this.after = 1; 
				changedState = true; 
			}
			

			$.ajax({
			    url : "/files/calendar?device="+_device,
				async: false,
				context: this,
			    success : function(result){
					//alert(JSON.stringify(result));
			    }
			});
		}

		if(_type != null) {
			if(this.type != _type) {
				changedState = true;
				this.after = 1; 
				$(".type").removeClass("selectedDevice");
				$("#type-"+_type).addClass("selectedDevice");
				this.type = _type; 				
			} else {
				changedState = true;
				this.after = 1; 
				$(".type").removeClass("selectedDevice");
				this.type = null;
			}
		}
	
		$.ajax({
		    url : "/files?after="+this.after+"&device="+this.device+"&format="+this.type,
			async: false,
			context: this,
		    success : function(result){
		    	if(changedState == true) {
					this.me.items = [];
				}

			    for(var i = 0; i < result.files.length; i++) {
			      var type_content = ""; 
			      
			      if(result.files[i].type == "video" && result.files[i].value != null) {
			      	  var video_length = result.files[i].value.split(" ")
			      	  var suffix = "ms"; 
			      	  
			      	  for (var ind = 0; ind < video_length.length; ++ind) {
			      	  	if(video_length[ind].indexOf(suffix, video_length[ind].length - suffix.length) == -1)
							type_content += video_length[ind].replace("mn", "min")+" ";
					  }
			      }			      
			      this.me.items.push({background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:result.files[i].type, type_content:type_content});
			    }			    

		        this.after = this.after + 1;
		        this.busy = false;		        
		    }
		});
	  };
	
	  return Infinity;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');

        $stateProvider
            .state('devices', {
                url: '/devices',
                controller: 'DevicesCtrl',
                templateUrl: '/templates/devices.html'
            })
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {

        ng.element($window).bind('scroll', function () {
            var winHeight = $($window).height();
            $('.preview.image').each(function () {
                var rect = this.getBoundingClientRect(),
                    el = $(this),
                    pos,
                    percent;
                if (rect.bottom >= 0 && rect.top <= winHeight) {
                    pos = rect.top / (winHeight - el.height());
                    percent = Math.round(Math.min(100, Math.max(0,
                                pos * 100)));
                    el.css('backgroundPosition', '50% ' + percent + '%');
                }
            });
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.filesResource = $resource('/files');
            this.filterResource = $resource('/files/filters');
            this.detailsResource = $resource('/files/details');
            this.deviceResource = $resource('/files/devices');
            this.calendarResource = $resource('/files/calendar');
            this.calendar = [];
            this.devices = [];
            this.files = [];
            this.filters = [];
            this.details = [];
        };
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function (resource) {
                this.files = resource.files;
                console.log(resource.sql);
            },

            /**
             * Successful filters load callback
             */
            loadFiltersSuccess: function (data) {
                this.filters = data.filters;
            },

            /**
             * Successful filters load callback
             */
            loadCalendarSuccess: function (data) {
                this.calendar = data;
            },

            /**
             * Successful filters load callback
             */
            loadDevicesSuccess: function (data) {
                this.devices = data.devices;
            },


            /**
             * Successful filters load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key

                if ($window.devicePixelRatio && $window.devicePixelRatio > 1) {
                    args.retina = 1;
                }

                if (typeof filter === 'object') {
                    for (fk in filter) {
                        if (filter.hasOwnProperty(fk) && filter[fk].length) {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    function (data) {
                        that.loadFilesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },


            /**
             * Load available calendar
             */
            loadCalendar: function () {
                this.calendarResource.get(
                    {},
                    this.loadCalendarSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load available devices
             */
            loadDevices: function () {
                this.deviceResource.get(
                    {},
                    this.loadDevicesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },
            
            /**
             * Load available filters
             */
            loadFilters: function () {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * Device service
     */
    box.factory('DeviceService', function ($resource, $window, $q) {

        /**
         *
         */
        var DeviceService = function () {
            this.devicesResource = $resource('/files/devices');
            this.devices = [];
        };
        DeivceService.prototype = {

            /**
             * Successful devices load callback
             */
            loadDevicesSuccess: function (resource) {
                this.devices = resource.devices;
                console.log(resource.sql);
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                console.log(data);
            },

            /**
             * Load devices passing 'devices'
             */
            loadDevices: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key


                this.devicesResource.get(
                    args,
                    function (data) {
                        that.loadDevicesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },

        };

        return new DeviceService();
    });


    /**
     * File thumbnail directive
     */
    box.directive('fileThumbnail', function ($window) {
        return {
            restrict: 'A',
            link: function (scope, element) {
                var el = ng.element(element),
                    file = scope.file,
                    imgUrl = '/static/images/';
                if (file.thumbnail) {
                    el.addClass('image')
                        .css('backgroundImage',
                                'url(' + imgUrl + file.thumbnail + ')')
			.find('img').attr('src', imgUrl + file.icon_small).hide();
			$($window).scroll(); // provoke background re-positioning
                } else {
                    el.addClass('icon')
                        .find('img').attr('src', imgUrl + file.icon_large);
                }
            }
        };
    });

    /**
     * File extension trim filter
     */
    box.filter('trimFileExtension', function () {
        return function (fileName) {
            var parts = fileName.split('.');
            if (parts.length >= 2) {
                parts.pop();
            }
            return parts.join('.');
        };
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $location, FileService, Infinity) {

        var that = this;
        this.fileService = FileService.loadFilters().loadFiles().loadDevices();
        $scope.infinity = new Infinity($scope);
        $scope.items = [];
        $scope.render = function(e) {
			return $(e).html();
        }
        
        this.filterState = {};
        this.isFilterPending = false;
        $('#filesDetailModal').modal({show: false})
                .on('hide.bs.modal', function () {
            $location.path('/');
            $scope.$apply();
        });

        $scope.FilesCtrl = this;
        return this;
    });

}(window, angular, jQuery, console || {log: function () { 'use strict'; return; }}));

